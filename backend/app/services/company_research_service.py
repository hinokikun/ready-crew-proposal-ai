from html import unescape
import re
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.models import CompanyResearchRequest, CompanyResearchResponse


PRIVATE_HOST_PREFIXES = ("localhost", "127.", "10.", "192.168.", "0.", "169.254.")


def normalize_public_url(value: str) -> str:
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


def extract_public_page_text(url: str) -> tuple[str, str, str]:
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


def build_company_research_response(
    payload: CompanyResearchRequest,
    fetched: bool,
    title: str,
    description: str,
    body: str,
) -> CompanyResearchResponse:
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
        recruitment="採用ページ、社員紹介、応募導線、更新頻度を確認します。"
        if _keyword_exists(combined_text, ["採用", "求人", "社員"])
        else "採用情報は公開有無と訴求内容を確認します。",
        news=["お知らせ更新頻度", "直近のサービス・採用・イベント告知", "CMSで継続更新できる情報設計"],
        services=services[:5],
        sns=["X / Instagram / Facebook / LinkedInの有無", "更新頻度", "サイト導線との接続", "採用・実績訴求への活用"],
    )


def _extract_meta_content(html: str, name: str) -> str:
    pattern = rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)["\']'
    match = re.search(pattern, html, flags=re.IGNORECASE)
    return unescape(match.group(1)).strip() if match else ""


def _keyword_exists(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text.lower() for keyword in keywords)
