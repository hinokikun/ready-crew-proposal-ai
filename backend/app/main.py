import base64
import hashlib
import hmac
from html import unescape
from io import BytesIO
import logging
import re
import time
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import (
    AnalysisResponse,
    AuthLoginRequest,
    AuthResponse,
    AuthStatusResponse,
    CompanyResearchRequest,
    CompanyResearchResponse,
    ProposalRequest,
    PptxDownloadRequest,
)
from app.services.openai_service import OpenAIServiceError, generate_proposal
from app.services.pdf_service import PDF_MEDIA_TYPE, build_estimate_pdf_bytes, build_estimate_pdf_filename
from app.services.pptx_service import MEDIA_TYPE, build_pptx_bytes, build_pptx_filename


logger = logging.getLogger(__name__)

PRIVATE_HOST_PREFIXES = ("localhost", "127.", "10.", "192.168.", "0.", "169.254.")


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _auth_configured() -> bool:
    return bool(settings.app_access_password and settings.app_auth_secret)


def _create_auth_token() -> str:
    issued_at = str(int(time.time()))
    signature = hmac.new(
        settings.app_auth_secret.encode("utf-8"),
        issued_at.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{_b64_encode(issued_at.encode('utf-8'))}.{_b64_encode(signature)}"


def _verify_auth_token(token: str) -> bool:
    if not _auth_configured() or "." not in token:
        return False
    encoded_issued_at, encoded_signature = token.split(".", 1)
    try:
        issued_at = _b64_decode(encoded_issued_at).decode("utf-8")
        issued_at_int = int(issued_at)
        provided_signature = _b64_decode(encoded_signature)
    except Exception:
        return False
    if int(time.time()) - issued_at_int > settings.app_auth_token_ttl_seconds:
        return False
    expected_signature = hmac.new(
        settings.app_auth_secret.encode("utf-8"),
        issued_at.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return hmac.compare_digest(provided_signature, expected_signature)


def require_auth(authorization: str | None = Header(default=None)) -> None:
    if not _auth_configured():
        raise HTTPException(status_code=503, detail="APP_ACCESS_PASSWORD が未設定です。Backendの環境変数を設定してください。")
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not _verify_auth_token(token):
        raise HTTPException(status_code=401, detail="ログインが必要です。再度ログインしてください。")


def _normalize_public_url(value: str) -> str:
    raw_url = value.strip()
    if not raw_url:
        raise ValueError("会社URLを入力してください。")
    normalized = raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}"
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or not host:
        raise ValueError("httpまたはhttpsの会社URLを入力してください。")
    if host.startswith(PRIVATE_HOST_PREFIXES) or host.endswith(".local"):
        raise ValueError("社内・ローカルURLは調査対象にできません。公開URLを入力してください。")
    if host.startswith("172."):
        second = host.split(".")[1] if len(host.split(".")) > 1 else ""
        if second.isdigit() and 16 <= int(second) <= 31:
            raise ValueError("プライベートIPのURLは調査対象にできません。")
    return normalized


def _extract_meta_content(html: str, name: str) -> str:
    pattern = rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']'
    match = re.search(pattern, html, flags=re.IGNORECASE)
    return unescape(match.group(1)).strip() if match else ""


def _extract_public_page_text(url: str) -> tuple[str, str, str]:
    request = Request(url, headers={"User-Agent": "ReadyCrewProposalAI/4.0"})
    with urlopen(request, timeout=6) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return "", "", ""
        html = response.read(250_000).decode("utf-8", errors="ignore")
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    title = unescape(re.sub(r"\s+", " ", title_match.group(1))).strip() if title_match else ""
    description = _extract_meta_content(html, "description") or _extract_meta_content(html, "og:description")
    body = re.sub(r"<(script|style).*?</\1>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    body = unescape(re.sub(r"<[^>]+>", " ", body))
    body = re.sub(r"\s+", " ", body).strip()[:3000]
    return title, description, body


def _keyword_exists(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)


def _build_company_research_response(payload: CompanyResearchRequest, fetched: bool, title: str, description: str, body: str) -> CompanyResearchResponse:
    source = payload.url.strip()
    combined_text = " ".join([title, description, body, payload.project_brief, payload.client_company_info])
    overview_base = title or description or payload.client_company_info or source
    competitors = ["検索結果上位の同業サイト", "地域・業種で比較される企業", "採用やサービス訴求が近い企業"]
    if _keyword_exists(combined_text, ["不動産", "物件", "住宅"]):
        competitors.insert(0, "地域大手の不動産会社")
    if _keyword_exists(combined_text, ["採用", "求人", "人材"]):
        competitors.insert(0, "採用競合企業")
    services = ["主力サービス", "導入事例・実績", "FAQ・問い合わせ導線"]
    if _keyword_exists(combined_text, ["CMS", "WordPress", "更新"]):
        services.append("CMS更新コンテンツ")
    if _keyword_exists(combined_text, ["SEO", "検索", "自然流入"]):
        services.append("SEOコンテンツ")
    return CompanyResearchResponse(
        source_url=source,
        fetched=fetched,
        overview=f"{overview_base} を起点に、会社概要・事業内容・顧客接点を確認しました。",
        competitors=competitors[:4],
        recruitment="採用ページ、社員紹介、応募導線、更新頻度を確認します。" if _keyword_exists(combined_text, ["採用", "求人", "社員"]) else "採用情報は公開有無と訴求内容を確認します。",
        news=["お知らせ更新頻度", "直近のサービス・採用・イベント告知", "CMSで継続更新できる情報設計"],
        services=services[:5],
        sns=["X / Instagram / Facebook / LinkedInの有無", "更新頻度", "サイト導線との接続", "採用・実績訴求への活用"],
    )

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
async def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "auth_configured": _auth_configured(),
        "mock_ai": settings.use_mock_ai,
        "ai_api": "mock" if settings.use_mock_ai else ("configured" if settings.openai_api_key else "missing"),
        "pptx": "available",
        "pdf": "available",
    }


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(payload: AuthLoginRequest) -> AuthResponse:
    if not _auth_configured():
        raise HTTPException(status_code=503, detail="APP_ACCESS_PASSWORD が未設定です。Backendの環境変数を設定してください。")
    if not hmac.compare_digest(payload.password, settings.app_access_password):
        raise HTTPException(status_code=401, detail="パスワードが正しくありません。")
    return AuthResponse(
        authenticated=True,
        token=_create_auth_token(),
        expires_in_seconds=settings.app_auth_token_ttl_seconds,
        message="ログインしました。",
    )


@app.get("/api/auth/status", response_model=AuthStatusResponse)
async def auth_status(_: None = Depends(require_auth)) -> AuthStatusResponse:
    return AuthStatusResponse(authenticated=True, auth_configured=_auth_configured())


@app.post("/api/company-research", response_model=CompanyResearchResponse)
async def company_research(payload: CompanyResearchRequest, _: None = Depends(require_auth)) -> CompanyResearchResponse:
    try:
        normalized_url = _normalize_public_url(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        title, description, body = _extract_public_page_text(normalized_url)
        return _build_company_research_response(payload.copy(update={"url": normalized_url}), True, title, description, body)
    except Exception:
        logger.exception("Failed to fetch company URL.")
        return _build_company_research_response(payload.copy(update={"url": normalized_url}), False, "", "", "")


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze(payload: ProposalRequest, _: None = Depends(require_auth)) -> AnalysisResponse:
    try:
        return await generate_proposal(payload)
    except OpenAIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@app.post("/api/download-pptx")
async def download_pptx(payload: PptxDownloadRequest, _: None = Depends(require_auth)) -> StreamingResponse:
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
async def download_summary_pptx(payload: PptxDownloadRequest, _: None = Depends(require_auth)) -> StreamingResponse:
    summary_payload = payload.copy(update={"summary": True})
    return await download_pptx(summary_payload, _)


@app.post("/api/download-estimate-pdf")
async def download_estimate_pdf(payload: PptxDownloadRequest, _: None = Depends(require_auth)) -> StreamingResponse:
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


