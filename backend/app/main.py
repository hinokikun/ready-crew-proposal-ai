from contextlib import asynccontextmanager
from io import BytesIO
import json
import logging
import time
from typing import Any
from urllib.parse import quote

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.config import settings
from app.auth import ensure_not_maintenance_mode, require_roles
from app.analytics.services import record_event
from app.db import get_db, get_db_health, init_db, seed_default_organization, seed_default_templates
from app.health import build_health_payload as build_application_health_payload
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
from app.router_registry import include_application_routers
from app.services.company_research_service import build_company_research_response, extract_public_page_text, normalize_public_url
from app.services.openai_service import OpenAIServiceError, generate_proposal
from app.services.pdf_service import PDF_MEDIA_TYPE, build_estimate_pdf_bytes, build_estimate_pdf_filename
from app.services.pptx_service import MEDIA_TYPE, build_pptx_filename
from app.services.customer_ready_quality import CustomerReadyBlockedError
from app.services.presentation_engine_integration import (
    ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP,
    RendererMvpInternalCanaryDisabled,
    RendererMvpInternalCanaryError,
    build_pptx_bytes_for_engine,
    build_renderer_mvp_internal_canary_pptx_bytes,
)
from app.services.proposal_metadata_service import extract_contact_person, extract_customer_name, proposal_input_length, pptx_input_length


logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


PRODUCTION_ENVIRONMENTS = {"production", "prod"}
LOCAL_ENVIRONMENTS = {"local", "development", "dev", "test", "testing"}


def _log_runtime_flag_config() -> None:
    """Emit the cached runtime flag state once during application startup."""
    try:
        logger.info(
            "presentation_shadow_runtime_config",
            extra={
                "shadow_enabled": bool(settings.presentation_master_v3_renderer_mvp_shadow_enabled),
                "pmv3_enabled": bool(settings.presentation_master_v3_renderer_mvp_enabled),
            },
        )
    except Exception:
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    _log_runtime_flag_config()
    init_db()
    db_tables_count = get_db_health().get("db_tables_count", 0)
    if db_tables_count:
        with get_db() as db:
            ensure_initial_admin(db)
            seed_default_organization(db)
        seed_default_templates()
    elif settings.initial_admin_email and settings.initial_admin_password:
        logger.warning("initial_admin_seed_skipped reason=no_database_tables")
    yield


app = FastAPI(
    title="Ready Crew Proposal AI Agent",
    description="Ready Crew の案件概要から業種を問わない営業提案書の初稿を生成するAPIです。",
    version=settings.app_version,
    lifespan=lifespan,
)

DEV_CORS_ORIGINS = {
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
}


def _is_local_environment() -> bool:
    return settings.environment.strip().lower() in LOCAL_ENVIRONMENTS


def _is_development_origin(origin: str) -> bool:
    normalized = origin.strip().lower()
    return normalized.startswith("http://localhost") or normalized.startswith("http://127.0.0.1")


def _resolved_cors_origins() -> list[str]:
    origins = {origin.strip() for origin in settings.cors_origins if origin.strip() and origin.strip() != "*"}
    if _is_local_environment():
        origins.update(DEV_CORS_ORIGINS)
    else:
        origins = {origin for origin in origins if not _is_development_origin(origin)}
    return sorted(origins)


def _resolved_cors_origin_regex() -> str | None:
    regex = settings.cors_origin_regex
    if not regex:
        return None
    if settings.environment.strip().lower() in PRODUCTION_ENVIRONMENTS and regex.strip() in {".*", "^.*$"}:
        logger.warning("Ignoring unsafe wildcard CORS regex in production.")
        return None
    return regex


app.add_middleware(
    CORSMiddleware,
    allow_origins=_resolved_cors_origins(),
    allow_origin_regex=_resolved_cors_origin_regex(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Organization-ID", "X-Workspace-ID"],
    expose_headers=["Content-Disposition", "X-Request-ID", "X-Presentation-Quality-Report"],
)


def _apply_security_headers(request: Request, response: Any) -> None:
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    if request.url.path not in {"/docs", "/redoc", "/openapi.json"}:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"
    if request.url.path.startswith(("/api", "/health")):
        response.headers["Cache-Control"] = "no-store"
    if settings.environment.strip().lower() in PRODUCTION_ENVIRONMENTS:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    _apply_security_headers(request, response)
    return response


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

include_application_routers(app)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Ready Crew Proposal AI Agent", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, Any]:
    return build_application_health_payload(app)


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
    payload = build_application_health_payload(app)
    status_code = 200 if payload["status"] == "ok" else 503
    return JSONResponse(payload, status_code=status_code)


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
    started = time.perf_counter()
    try:
        response = await generate_proposal(payload)
        duration_ms = perf_counter_ms(started)
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
            customer_id = get_or_create_customer(db, extract_customer_name(payload), "", extract_contact_person(payload), user_id=int(user["id"]))
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
                project_name=response.powerpoint_generation_data.deck_title or response.analysis.project_summary,
                proposal_generation_duration_ms=duration_ms,
            )
        return response
    except OpenAIServiceError as exc:
        duration_ms = perf_counter_ms(started)
        with get_db() as db:
            create_history_log(
                db,
                int(user["id"]),
                None,
                None,
                "提案書生成",
                proposal_input_length(payload),
                "markdown",
                "failure",
                "OpenAI API",
                project_name=payload.project_brief[:120],
                proposal_generation_duration_ms=duration_ms,
            )
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.post("/api/download-pptx")
async def download_pptx(
    request: Request,
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
    started = time.perf_counter()
    try:
        if not payload.summary and payload.candidate_boundary_correlation_id:
            raw_candidates = payload.semantic_candidates
            candidate_items = raw_candidates.get("candidates") if isinstance(raw_candidates, dict) else None
            candidate_count = len(candidate_items) if isinstance(candidate_items, list) else 0
            candidate_state = "OMITTED" if raw_candidates is None else ("NONEMPTY" if candidate_count else "EMPTY")
            try:
                with get_db() as db:
                    record_event(
                        db,
                        user_id=int(user["id"]),
                        session_key=f"candidate-boundary:{payload.candidate_boundary_correlation_id}",
                        event_name="presentation_candidate_boundary_backend",
                        feature_name="proposal",
                        status="success",
                        metadata={
                            "candidate_boundary_correlation_id": payload.candidate_boundary_correlation_id,
                            "semantic_candidates_state": candidate_state,
                            "candidate_count": candidate_count,
                        },
                    )
            except Exception as exc:
                logger.warning("diagnostic backend boundary capture failed: %s", exc.__class__.__name__)
                raise HTTPException(
                    status_code=503,
                    detail={"error_code": "DIAGNOSTIC_BACKEND_CAPTURE_FAILED", "message": "診断境界の保存に失敗しました。"},
                ) from exc
        engine_result = build_pptx_bytes_for_engine(
            payload,
            shadow_master=settings.presentation_design_ai_master_shadow_enabled,
            request_id=getattr(request.state, "request_id", ""),
        )
        duration_ms = perf_counter_ms(started)
        pptx_bytes = engine_result.pptx_bytes
        quality_report = engine_result.quality_report or {}
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
                project_name=payload.powerpoint_generation_data.deck_title,
                powerpoint_generation_duration_ms=duration_ms,
            )
    except CustomerReadyBlockedError as exc:
        logger.info(
            "customer_ready_quality_gate_blocked",
            extra={
                "status": exc.result.status,
                "score": exc.result.score,
                "blocker_count": len(exc.result.blockers),
            },
        )
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "CUSTOMER_READY_BLOCKED",
                "status": exc.result.status,
                "score": exc.result.score,
                "reasons": exc.result.reasons,
                "blockers": exc.result.blockers,
            },
        ) from exc
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
            "X-Presentation-Quality-Report": quote(
                json.dumps(quality_report, ensure_ascii=False, separators=(",", ":")),
                safe="",
            ),
        },
    )


@app.post("/api/internal/presentation-master-v3/canary/download-pptx")
async def download_internal_presentation_master_v3_canary_pptx(
    request: Request,
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin")),
    _: None = Depends(rate_limit_dependency("admin")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
    request_id = getattr(request.state, "request_id", "")
    started = time.perf_counter()
    try:
        engine_result = build_renderer_mvp_internal_canary_pptx_bytes(
            payload,
            request_id=request_id,
        )
        duration_ms = perf_counter_ms(started)
        pptx_bytes = engine_result.pptx_bytes
        quality_report = dict(engine_result.quality_report or {})
        filename = build_pptx_filename(
            payload.powerpoint_generation_data,
            payload.client_company_info,
            summary_mode=payload.summary,
        )
        encoded_filename = quote(f"v3-canary-{filename}")
        logger.info(
            "v3_internal_canary_response_prepared",
            extra={
                "requested_version": ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP,
                "actual_version": engine_result.engine_mode,
                "fallback_used": False,
                "fallback_reason": "",
                "request_id": request_id,
                "duration_ms": duration_ms,
                "role": str(user.get("role", "")),
            },
        )
    except RendererMvpInternalCanaryDisabled as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error_type": "internal_canary_disabled",
                "message": "Presentation Master V3 internal Canary is disabled.",
                "request_id": request_id,
                "fallback_used": False,
                "fallback_reason": exc.reason_code,
            },
        ) from exc
    except RendererMvpInternalCanaryError as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "internal_canary_generation_failed",
                "message": "Presentation Master V3 internal Canary generation failed.",
                "request_id": request_id,
                "fallback_used": False,
                "fallback_reason": exc.reason_code,
                "fallback_category": exc.fallback_category,
                "failure_stage": exc.failure_stage,
            },
        ) from exc
    except Exception as exc:
        logger.exception(
            "v3_internal_canary_unexpected_failure",
            extra={
                "requested_version": ENGINE_MODE_PRESENTATION_MASTER_V3_RENDERER_MVP,
                "actual_version": "",
                "fallback_used": False,
                "fallback_reason": exc.__class__.__name__,
                "request_id": request_id,
            },
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error_type": "internal_canary_unexpected_failure",
                "message": "Presentation Master V3 internal Canary generation failed.",
                "request_id": request_id,
                "fallback_used": False,
                "fallback_reason": exc.__class__.__name__,
            },
        ) from exc

    return StreamingResponse(
        BytesIO(pptx_bytes),
        media_type=MEDIA_TYPE,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "X-Presentation-Engine": "renderer-mvp-v3",
            "X-Presentation-Canary": "true",
            "X-Presentation-Canary-Success": "true",
            "X-Presentation-Quality-Report": quote(
                json.dumps(quality_report, ensure_ascii=False, separators=(",", ":")),
                safe="",
            ),
        },
    )


@app.post("/api/download-summary-pptx")
async def download_summary_pptx(
    request: Request,
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
    summary_payload = payload.copy(update={"summary": True})
    return await download_pptx(request, summary_payload, user)


@app.post("/api/download-estimate-pdf")
async def download_estimate_pdf(
    payload: PptxDownloadRequest,
    user: dict = Depends(require_roles("admin", "member")),
    _: None = Depends(rate_limit_dependency("generation")),
) -> StreamingResponse:
    ensure_not_maintenance_mode()
    started = time.perf_counter()
    try:
        pdf_bytes = build_estimate_pdf_bytes(payload)
        duration_ms = perf_counter_ms(started)
        filename = build_estimate_pdf_filename(payload)
        encoded_filename = quote(filename)
        with get_db() as db:
            create_history_log(
                db,
                int(user["id"]),
                None,
                None,
                "見積書PDF",
                pptx_input_length(payload),
                "estimate-pdf",
                "success",
                project_name=payload.powerpoint_generation_data.deck_title,
                pdf_generation_duration_ms=duration_ms,
            )
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


