from io import BytesIO
import logging
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.auth import require_roles
from app.db import check_db, get_db, init_db
from app.models import (
    AnalysisResponse,
    CompanyResearchRequest,
    CompanyResearchResponse,
    ProposalRequest,
    PptxDownloadRequest,
)
from app.repositories import create_history_log, ensure_initial_admin, get_or_create_customer, get_or_create_project
from app.routers import auth as auth_router
from app.routers import feedback as feedback_router
from app.routers import logs as logs_router
from app.routers import projects as projects_router
from app.routers import users as users_router
from app.services.company_research_service import build_company_research_response, extract_public_page_text, normalize_public_url
from app.services.openai_service import OpenAIServiceError, generate_proposal
from app.services.pdf_service import PDF_MEDIA_TYPE, build_estimate_pdf_bytes, build_estimate_pdf_filename
from app.services.pptx_service import MEDIA_TYPE, build_pptx_bytes, build_pptx_filename
from app.services.proposal_metadata_service import extract_contact_person, extract_customer_name, proposal_input_length, pptx_input_length


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ready Crew Proposal AI Agent",
    description="Ready Crew の案件概要からWeb制作提案書の初稿を生成するMVP APIです。",
    version="0.1.0",
)

DEV_CORS_ORIGINS = {
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted({*settings.cors_origins, *DEV_CORS_ORIGINS}),
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(projects_router.router)
app.include_router(logs_router.router)
app.include_router(feedback_router.router)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    with get_db() as db:
        ensure_initial_admin(db)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Ready Crew Proposal AI Agent", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "auth_configured": bool(settings.app_auth_secret and (settings.initial_admin_email or settings.app_access_password)),
        "mock_ai": settings.use_mock_ai,
        "ai_api": "mock" if settings.use_mock_ai else ("configured" if settings.openai_api_key else "missing"),
        "pptx": "available",
        "pdf": "available",
        "db": "connected" if check_db() else "error",
    }


@app.post("/api/company-research", response_model=CompanyResearchResponse)
async def company_research(payload: CompanyResearchRequest, _: dict = Depends(require_roles("admin", "member"))) -> CompanyResearchResponse:
    try:
        normalized_url = normalize_public_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        title, description, body = extract_public_page_text(normalized_url)
        return build_company_research_response(payload.copy(update={"url": normalized_url}), True, title, description, body)
    except Exception:
        logger.exception("Failed to fetch company URL.")
        return build_company_research_response(payload.copy(update={"url": normalized_url}), False, "", "", "")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(payload: ProposalRequest, user: dict = Depends(require_roles("admin", "member"))) -> AnalysisResponse:
    try:
        response = await generate_proposal(payload)
        with get_db() as db:
            customer_id = get_or_create_customer(db, extract_customer_name(payload), "", extract_contact_person(payload))
            project_id = get_or_create_project(
                db,
                customer_id,
                response.powerpoint_generation_data.deck_title or "提案書生成案件",
                response.analysis.project_summary,
                response.analysis.win_probability.probability,
                "次回確認事項を整理し、提案資料を人が確認します。",
            )
            create_history_log(
                db,
                int(user["id"]),
                customer_id,
                project_id,
                "提案書生成",
                proposal_input_length(payload),
                "markdown+pptx-data",
                "success",
            )
        return response
    except OpenAIServiceError as exc:
        with get_db() as db:
            create_history_log(db, int(user["id"]), None, None, "提案書生成", proposal_input_length(payload), "markdown", "failure", "OpenAI API")
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.post("/api/download-pptx")
async def download_pptx(payload: PptxDownloadRequest, user: dict = Depends(require_roles("admin", "member"))) -> StreamingResponse:
    try:
        pptx_bytes = build_pptx_bytes(payload)
        filename = build_pptx_filename(
            payload.powerpoint_generation_data,
            payload.client_company_info,
            summary_mode=payload.summary,
        )
        encoded_filename = quote(filename)
        with get_db() as db:
            create_history_log(
                db,
                int(user["id"]),
                None,
                None,
                "要約PowerPoint" if payload.summary else "PowerPoint",
                pptx_input_length(payload),
                "summary-pptx" if payload.summary else "pptx",
                "success",
            )
    except Exception as exc:
        logger.exception("Failed to generate PowerPoint download. summary=%s", payload.summary)
        detail = (
            "要約PowerPoint生成中にエラーが発生しました。バックエンドログを確認してください。"
            if payload.summary
            else "PowerPoint生成中にエラーが発生しました。バックエンドログを確認してください。"
        )
        raise HTTPException(status_code=500, detail=detail) from exc

    return StreamingResponse(
        BytesIO(pptx_bytes),
        media_type=MEDIA_TYPE,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


@app.post("/api/download-summary-pptx")
async def download_summary_pptx(payload: PptxDownloadRequest, user: dict = Depends(require_roles("admin", "member"))) -> StreamingResponse:
    summary_payload = payload.copy(update={"summary": True})
    return await download_pptx(summary_payload, user)


@app.post("/api/download-estimate-pdf")
async def download_estimate_pdf(payload: PptxDownloadRequest, user: dict = Depends(require_roles("admin", "member"))) -> StreamingResponse:
    try:
        pdf_bytes = build_estimate_pdf_bytes(payload)
        filename = build_estimate_pdf_filename(payload)
        encoded_filename = quote(filename)
        with get_db() as db:
            create_history_log(db, int(user["id"]), None, None, "見積書PDF", pptx_input_length(payload), "estimate-pdf", "success")
    except Exception as exc:
        logger.exception("Failed to generate estimate PDF download.")
        raise HTTPException(
            status_code=500,
            detail="見積書PDF生成中にエラーが発生しました。バックエンドログを確認してください。",
        ) from exc

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type=PDF_MEDIA_TYPE,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
        },
    )


