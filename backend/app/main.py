from contextlib import asynccontextmanager
from io import BytesIO
import logging
import time
from typing import Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import settings
from app.auth import ensure_not_maintenance_mode, require_roles
from app.db import get_db, get_db_health, init_db, seed_default_templates
from app.knowledge.services import add_knowledge_entry, build_best_practices, search_similar_knowledge
from app.models import (
    AnalysisResponse,
    CompanyResearchRequest,
    CompanyResearchResponse,
    ProposalRequest,
    PptxDownloadRequest,
)
from app.observability import get_request_role, log_structured, new_request_id, perf_counter_ms, report_error, utc_timestamp
from app.rate_limit import rate_limit_dependency
from app.repositories import create_history_log, ensure_initial_admin, get_or_create_customer, get_or_create_project
from app.prompts.repositories import record_prompt_metric, select_prompt_version_for_project
from app.routers import analytics as analytics_router
from app.routers import auth as auth_router
from app.routers import beautiful_ai as beautiful_ai_router
from app.routers import briefing as briefing_router
from app.routers import feedback as feedback_router
from app.routers import integrations as integrations_router
from app.routers import knowledge as knowledge_router
from app.routers import learning as learning_router
from app.routers import logs as logs_router
from app.routers import notifications as notifications_router
from app.routers import orchestrator as orchestrator_router
from app.routers import pilot as pilot_router
from app.routers import prompts as prompts_router
from app.routers import projects as projects_router
from app.routers import quality_gates as quality_gates_router
from app.routers import releases as releases_router
from app.routers import reviews as reviews_router
from app.routers import users as users_router
from app.routers import workspace as workspace_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if get_db_health().get("db_tables_count", 0):
        with get_db() as db:
            ensure_initial_admin(db)
        seed_default_templates()
    yield


app = FastAPI(
    title="Ready Crew Proposal AI Agent",
    description="Ready Crew の案件概要からWeb制作提案書の初稿を生成するMVP APIです。",
    version=settings.app_version,
    lifespan=lifespan,
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
    expose_headers=["Content-Disposition", "X-Request-ID"],
)


@app.middleware("http")
async def request_observability_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or new_request_id()
    request.state.request_id = request_id
    started_at = time.perf_counter()
    status_code = 500
    error_type = ""
    response = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as exc:
        error_type = exc.__class__.__name__
        report_error(
            exc,
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
            logger,
        )
        raise
    finally:
        duration_ms = perf_counter_ms(started_at)
        log_structured(
            logger,
            "info" if status_code < 500 else "error",
            "http_request",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            user_role=get_request_role(request),
            error_type=error_type,
        )
        if response is not None:
            response.headers["X-Request-ID"] = request_id


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "") or new_request_id()
    headers = dict(exc.headers or {})
    headers["X-Request-ID"] = request_id
    if exc.status_code in {429, 503} and isinstance(exc.detail, dict):
        body = dict(exc.detail)
        body["request_id"] = body.get("request_id") or request_id
        return JSONResponse(body, status_code=exc.status_code, headers=headers)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=headers)

app.include_router(auth_router.router)
app.include_router(users_router.router)
app.include_router(briefing_router.router)
app.include_router(notifications_router.router)
app.include_router(orchestrator_router.router)
app.include_router(pilot_router.router)
app.include_router(projects_router.router)
app.include_router(logs_router.router)
app.include_router(feedback_router.router)
app.include_router(integrations_router.router)
app.include_router(analytics_router.router)
app.include_router(knowledge_router.router)
app.include_router(learning_router.router)
app.include_router(prompts_router.router)
app.include_router(workspace_router.router)
app.include_router(reviews_router.router)
app.include_router(quality_gates_router.router)
app.include_router(releases_router.router)
app.include_router(beautiful_ai_router.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Ready Crew Proposal AI Agent", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, Any]:
    return build_health_payload()


@app.get("/health/live")
async def health_live() -> dict[str, Any]:
    return {
        "status": "ok",
        "app_version": settings.app_version,
        "environment": settings.environment,
        "timestamp": utc_timestamp(),
    }


@app.get("/health/ready")
async def health_ready() -> JSONResponse:
    payload = build_health_payload()
    status_code = 200 if payload["status"] == "ok" else 503
    return JSONResponse(payload, status_code=status_code)


def build_health_payload() -> dict[str, Any]:
    db_health = get_db_health()
    auth_configured = bool(settings.app_auth_secret and (settings.initial_admin_email or settings.app_access_password))
    db_connected = bool(db_health["db_connected"])
    db_ready = db_connected and int(db_health.get("db_tables_count", 0)) > 0
    ai_api = "mock" if settings.use_mock_ai else ("configured" if settings.openai_api_key else "missing")
    ready = auth_configured and db_ready and ai_api != "missing"
    return {
        "status": "ok" if ready else "degraded",
        "app_version": settings.app_version,
        "environment": settings.environment,
        "auth_configured": auth_configured,
        "pilot_mode": settings.pilot_mode,
        "pilot_start_date": settings.pilot_start_date,
        "pilot_end_date": settings.pilot_end_date,
        "pilot_max_users": settings.pilot_max_users,
        "maintenance_mode": settings.maintenance_mode,
        "mock_ai": settings.use_mock_ai,
        "ai_api": ai_api,
        "pptx": "available",
        "pdf": "available",
        "db": "connected" if db_connected else "error",
        "db_connected": db_connected,
        "db_type": db_health["db_type"],
        "db_tables_count": db_health["db_tables_count"],
        "startup_schema_migration_enabled": db_health.get("startup_schema_migration_enabled", False),
        "timestamp": utc_timestamp(),
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
async def analyze(
    payload: ProposalRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> AnalysisResponse:
    ensure_not_maintenance_mode()
    try:
        response = await generate_proposal(payload)
        with get_db() as db:
            knowledge_insights = search_similar_knowledge(db, response.analysis.project_summary or payload.project_brief, "", 4)
            response.knowledge_insights = {
                "similar": knowledge_insights,
                "best_practices": build_best_practices(db),
            }
            add_knowledge_entry(
                db,
                {
                    "industry": knowledge_insights.get("industry", "other"),
                    "company_size": "",
                    "project_summary": response.analysis.project_summary,
                    "adopted_proposal": response.analysis.proposal_policy,
                    "proposal_story": response.analysis.proposal_story,
                    "adoption_reason": "",
                    "lost_reason": "",
                    "result": "",
                    "owner_memo": "Auto-saved summary from proposal generation.",
                    "outcome": "unknown",
                    "rating": 3,
                    "evaluation_status": "effective",
                    "tags": "auto_saved,proposal_generation",
                    "approval_status": "draft",
                    "source_type": "proposal_generated",
                    "source_note": "Auto-saved summary from proposal generation.",
                },
                int(user["id"]),
            )
            customer_id = get_or_create_customer(db, extract_customer_name(payload), "", extract_contact_person(payload))
            project_id = get_or_create_project(
                db,
                customer_id,
                response.powerpoint_generation_data.deck_title or "提案書生成案件",
                response.analysis.project_summary,
                response.analysis.win_probability.probability,
                "次回確認事項を整理し、提案資料を人が確認します。",
            )
            prompt_routing = select_prompt_version_for_project(db, prompt_name="proposal_generation", project_id=project_id, user_id=int(user["id"]))
            if prompt_routing.get("version") != "default":
                record_prompt_metric(
                    db,
                    experiment_id=prompt_routing.get("experiment_id"),
                    prompt_name="proposal_generation",
                    prompt_version=str(prompt_routing.get("version", "")),
                    project_id=project_id,
                    outcome="pending",
                    review_count=0,
                    quality_gate_passed=False,
                    proposal_time_seconds=0,
                    user_rating="",
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
async def download_pptx(
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
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
async def download_summary_pptx(
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
    summary_payload = payload.copy(update={"summary": True})
    return await download_pptx(summary_payload, user)


@app.post("/api/download-estimate-pdf")
async def download_estimate_pdf(
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
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


