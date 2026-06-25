from io import BytesIO
import logging
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import AnalysisResponse, ProposalRequest, PptxDownloadRequest
from app.services.openai_service import OpenAIServiceError, generate_proposal
from app.services.pdf_service import PDF_MEDIA_TYPE, build_estimate_pdf_bytes, build_estimate_pdf_filename
from app.services.pptx_service import MEDIA_TYPE, build_pptx_bytes, build_pptx_filename


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


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Ready Crew Proposal AI Agent", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(payload: ProposalRequest) -> AnalysisResponse:
    try:
        return await generate_proposal(payload)
    except OpenAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.post("/api/download-pptx")
async def download_pptx(payload: PptxDownloadRequest) -> StreamingResponse:
    try:
        pptx_bytes = build_pptx_bytes(payload)
        filename = build_pptx_filename(
            payload.powerpoint_generation_data,
            payload.client_company_info,
            summary_mode=payload.summary,
        )
        encoded_filename = quote(filename)
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
async def download_summary_pptx(payload: PptxDownloadRequest) -> StreamingResponse:
    summary_payload = payload.model_copy(update={"summary": True})
    return await download_pptx(summary_payload)


@app.post("/api/download-estimate-pdf")
async def download_estimate_pdf(payload: PptxDownloadRequest) -> StreamingResponse:
    try:
        pdf_bytes = build_estimate_pdf_bytes(payload)
        filename = build_estimate_pdf_filename(payload)
        encoded_filename = quote(filename)
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


