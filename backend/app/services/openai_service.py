import json
import re
from typing import Any

from fastapi.concurrency import run_in_threadpool
from openai import OpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from app.config import settings
from app.models import AnalysisResponse, ProposalAnalysis, ProposalRequest
from app.prompts import BASIC_PROPOSAL_STRUCTURE, SYSTEM_PROMPT, build_user_prompt
from app.schemas import PROPOSAL_ANALYSIS_SCHEMA
from app.utils.markdown import build_markdown


class OpenAIServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


async def generate_proposal(payload: ProposalRequest) -> AnalysisResponse:
    if settings.use_mock_ai:
        analysis = _build_mock_analysis(payload)
    else:
        analysis = await run_in_threadpool(_generate_with_openai, payload)

    markdown = build_markdown(analysis)
    return AnalysisResponse(
        analysis=analysis,
        markdown=markdown,
        powerpoint_generation_data=analysis.powerpoint_generation_data,
    )


def _generate_with_openai(payload: ProposalRequest) -> ProposalAnalysis:
    if not settings.openai_api_key:
        raise OpenAIServiceError(
            "OPENAI_API_KEY が未設定です。ローカルでは backend/.env、RenderではSecretsにAPIキーを設定してください。",
            status_code=400,
        )

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.request_timeout_seconds,
    )

    try:
        response = client.responses.create(
            model=settings.openai_model,
            instructions=SYSTEM_PROMPT,
            input=build_user_prompt(payload),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "ready_crew_proposal_analysis",
                    "schema": PROPOSAL_ANALYSIS_SCHEMA,
                    "strict": True,
                }
            },
            max_output_tokens=10000,
        )
    except AuthenticationError as exc:
        raise OpenAIServiceError("OpenAI API の認証に失敗しました。APIキーを確認してください。", 401) from exc
    except RateLimitError as exc:
        raise OpenAIServiceError("OpenAI API のレート制限に達した可能性があります。時間を置いて再実行してください。", 429) from exc
    except APITimeoutError as exc:
        raise OpenAIServiceError("OpenAI API の応答がタイムアウトしました。入力を短くするか再実行してください。", 504) from exc
    except APIConnectionError as exc:
        raise OpenAIServiceError("OpenAI API への接続に失敗しました。ネットワーク設定を確認してください。", 502) from exc
    except APIStatusError as exc:
        raise OpenAIServiceError(f"OpenAI API エラー: {exc.status_code} {exc.message}", exc.status_code) from exc

    raw_text = _extract_output_text(response)

    try:
        data = json.loads(raw_text)
        return ProposalAnalysis.model_validate(data)
    except json.JSONDecodeError as exc:
        raise OpenAIServiceError("AIの出力をJSONとして解析できませんでした。再実行してください。") from exc
    except ValidationError as exc:
        raise OpenAIServiceError(f"AIの出力形式が想定と異なります: {exc}") from exc


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                chunks.append(text)

    if chunks:
        return "".join(chunks)

    raise OpenAIServiceError("AIの応答テキストを取得できませんでした。")


def _extract_input_signals(payload: ProposalRequest) -> dict[str, Any]:
    full_text = "\n".join(
        [
            payload.project_brief,
            payload.client_company_info,
            payload.competitor_site_url,
            payload.competitor_company_name,
            payload.estimated_page_count,
            payload.cms_required,
            payload.contact_form_required,
            payload.special_function_required,
            payload.seo_required,
            payload.content_creation_required,
            payload.desired_launch_timing,
            payload.budget_range,
            payload.hearing_result,
            payload.own_service_info,
            payload.past_proposal_template,
            payload.case_studies,
        ]
    )
    needs = _unique_texts(
        [
            "問い合わせ導線・CTA改善" if _contains_any(full_text, ["問い合わせ", "問合せ", "CV", "コンバージョン"]) else "",
            "採用情報・応募導線強化" if "採用" in full_text else "",
            "現行サイトのリニューアル" if _contains_any(full_text, ["リニューアル", "刷新", "改修"]) else "",
            "情報設計・サービス訴求整理" if _contains_any(full_text, ["情報が古", "伝わりにく", "サービス内容", "訴求"]) else "",
            "CMS・更新運用の整理" if _contains_any(full_text, ["CMS", "更新"]) else "",
            "SEO・検索流入対策" if _contains_any(full_text, ["SEO", "検索"]) else "",
            "公開後の運用保守" if _contains_any(full_text, ["運用", "保守", "改善"]) else "",
        ],
        4,
    )
    if not needs:
        needs = ["Webサイトの役割整理", "成果につながる導線設計", "公開後の改善方針整理"]

    services = _extract_text_items(payload.own_service_info, 4)
    if not services:
        services = ["情報設計", "Webサイト制作", "公開後の改善運用支援"]

    cases = _extract_text_items(payload.case_studies, 3)
    if not cases:
        cases = ["近しい課題の成功事例を提案時に差し替え", "成果につながった進め方を紹介"]

    confirmations = _build_confirmation_items(full_text)
    template_sections = [section for section in BASIC_PROPOSAL_STRUCTURE if section in payload.past_proposal_template]

    has_budget_detail = "予算" in full_text and not _contains_any(full_text, ["予算は未定", "予算未定", "予算感未定"])
    concept = _derive_concept(full_text)
    current_state, business_issue, opportunity, target_state = _derive_understanding(full_text, needs, concept)
    estimate = _derive_estimate_summary(payload, full_text)

    return {
        "needs": needs,
        "services": services,
        "cases": cases,
        "confirmations": confirmations,
        "template_sections": template_sections,
        "concept": concept,
        "current_state": current_state,
        "business_issue": business_issue,
        "opportunity": opportunity,
        "target_state": target_state,
        "journey": _derive_journey(concept),
        "sitemap": _derive_sitemap(full_text),
        "kpi": _derive_kpi(concept, full_text),
        "competitor": _derive_competitor_analysis(full_text),
        "winning_strategy": _derive_winning_strategy(full_text),
        "targets": _derive_target_users(full_text, concept),
        "content": _derive_content_plan(full_text, concept),
        "web_strategy": _derive_web_strategy(concept, needs),
        "estimate": estimate,
        "budget_fit": estimate["budget_fit"],
        "has_budget": has_budget_detail,
        "has_deadline": _contains_any(full_text, ["納期", "公開時期", "公開希望", "リリース希望", "スケジュール", "早め", "急ぎ"]),
        "has_cms": _contains_any(full_text, ["CMS", "更新"]),
        "has_seo": _contains_any(full_text, ["SEO", "検索"]),
        "has_operation": _contains_any(full_text, ["運用", "保守", "改善"]),
        "has_competitor": bool(payload.competitor_site_url.strip() or payload.competitor_company_name.strip())
        or _contains_any(full_text, ["競合", "他社", "比較", "ベンチマーク", "差別化"]),
    }


def _derive_concept(text: str) -> str:
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        return "物件検索強化"
    if _contains_any(text, ["採用", "応募", "求人", "求職"]):
        return "採用強化"
    if _contains_any(text, ["問い合わせ", "問合せ", "CV", "コンバージョン", "資料請求", "商談"]):
        return "問い合わせ最大化"
    if _contains_any(text, ["ブランド", "ブランディング", "認知", "信頼感"]):
        return "ブランディング強化"
    if _contains_any(text, ["SEO", "検索", "流入"]):
        return "検索流入強化"
    if _contains_any(text, ["CMS", "更新", "運用"]):
        return "CMS運用強化"
    return "Web成果最大化"


def _derive_understanding(text: str, needs: list[str], concept: str) -> tuple[str, str, str, str]:
    current_state = "現行サイトの役割を見直し、営業・採用・広報の成果接点として再設計する局面です。"
    if _contains_any(text, ["古", "リニューアル", "刷新", "改修"]):
        current_state = "現行サイトの情報鮮度と見せ方が、現在の事業内容や営業活動に追いついていない状態です。"
    elif _contains_any(text, ["新規", "立ち上げ", "初めて"]):
        current_state = "新しいWeb接点を立ち上げ、事業内容と強みを伝える土台を作る局面です。"
    elif _contains_any(text, ["問い合わせ", "問合せ", "CV"]):
        current_state = "Webサイトを問い合わせ獲得の接点として強化する段階です。"

    business_issue = _issue_from_need(needs[0]) if needs else "Webサイトの役割と優先ターゲットを明確にする段階です。"
    opportunity_map = {
        "問い合わせ最大化": "導線、CTA、実績訴求を連動させ、商談につながる問い合わせを増やします。",
        "採用強化": "仕事内容、働く魅力、応募導線を整理し、候補者の理解と応募行動を促します。",
        "ブランディング強化": "強み、実績、メッセージを統一し、第一印象と信頼感を高めます。",
        "物件検索強化": "検索導線と物件情報を整理し、比較検討から問い合わせまでを短縮します。",
        "検索流入強化": "検索意図に合う構造とコンテンツを設計し、自然検索からの流入を伸ばします。",
        "CMS運用強化": "更新しやすいCMSと運用フローを整備し、情報鮮度を維持します。",
        "Web成果最大化": "情報設計、導線、運用を整え、Webサイトを成果創出の基盤にします。",
    }
    opportunity = opportunity_map.get(concept, opportunity_map["Web成果最大化"])
    target_state = f"{concept}を軸に、訪問者が理解、比較、問い合わせまで迷わず進める状態を作ります。"
    return current_state, business_issue, opportunity, target_state


def _derive_journey(concept: str) -> list[str]:
    if concept == "採用強化":
        return ["認知: 企業の魅力と募集職種を伝える", "比較検討: 働き方・社員情報・制度で納得感を高める", "問い合わせ: 応募フォームまでの導線を短くする"]
    if concept == "物件検索強化":
        return ["認知: エリア・物件情報への入口を増やす", "比較検討: 条件検索と物件詳細で比較しやすくする", "問い合わせ: 内見予約・資料請求へ迷わず進める"]
    if concept == "ブランディング強化":
        return ["認知: 企業の強みと世界観を第一印象で伝える", "比較検討: 実績・サービス・選ばれる理由を深く見せる", "問い合わせ: 相談したいテーマ別に導線を分ける"]
    return ["認知: SEO・広告・紹介からの受け皿を整える", "比較検討: サービス内容・実績・FAQで不安を減らす", "問い合わせ: CTAとフォーム導線を最短化する"]


def _derive_sitemap(text: str) -> list[str]:
    items = ["トップ", "会社案内", "サービス", "実績", "お知らせ", "お問い合わせ"]
    if _contains_any(text, ["採用", "求人", "応募"]):
        items.insert(-1, "採用情報")
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        items.insert(2, "物件検索")
    if _contains_any(text, ["CMS", "FAQ", "よくある質問"]):
        items.insert(-1, "FAQ")
    if _contains_any(text, ["資料請求", "ホワイトペーパー"]):
        items.insert(-1, "資料ダウンロード")
    return _unique_texts(items, 9)


def _derive_kpi(concept: str, text: str) -> list[str]:
    targets = _derive_kpi_targets(concept, text)
    if concept == "採用強化":
        return [f"問い合わせ数: 月{targets['inquiries']}件", f"CV率: {targets['cv_rate']}%", f"自然検索流入: 月{targets['organic']}セッション", f"資料DL数: 月{targets['downloads']}件"]
    if concept == "物件検索強化":
        return [f"問い合わせ数: 月{targets['inquiries']}件", f"CV率: {targets['cv_rate']}%", f"自然検索流入: 月{targets['organic']}セッション", f"資料DL数: 月{targets['downloads']}件"]
    return [f"問い合わせ数: 月{targets['inquiries']}件", f"CV率: {targets['cv_rate']}%", f"自然検索流入: 月{targets['organic']}セッション", f"資料DL数: 月{targets['downloads']}件"]


def _derive_kpi_targets(concept: str, text: str) -> dict[str, int | float]:
    if concept == "採用強化":
        return {"inquiries": 8, "cv_rate": 2.0, "organic": 2500, "downloads": 10}
    if concept == "物件検索強化":
        return {"inquiries": 25, "cv_rate": 3.0, "organic": 4000, "downloads": 20}
    if _contains_any(text, ["SEO", "検索", "流入"]):
        return {"inquiries": 18, "cv_rate": 2.5, "organic": 5000, "downloads": 30}
    if _contains_any(text, ["問い合わせ", "問合せ", "CV"]):
        return {"inquiries": 20, "cv_rate": 2.8, "organic": 3500, "downloads": 25}
    return {"inquiries": 12, "cv_rate": 2.0, "organic": 2500, "downloads": 15}


def _derive_competitor_analysis(text: str) -> list[str]:
    design = 2 if _contains_any(text, ["古", "リニューアル", "刷新"]) else 3
    search = 2 if _contains_any(text, ["SEO", "検索", "流入"]) else 3
    conversion = 2 if _contains_any(text, ["問い合わせ", "問合せ", "CV"]) else 3
    cms = 2 if _contains_any(text, ["CMS", "更新"]) else 3
    content = 2 if _contains_any(text, ["情報が古", "コンテンツ", "サービス内容", "実績"]) else 3
    cta = 2 if _contains_any(text, ["CTA", "問い合わせ", "問合せ", "CV"]) else 3
    return [
        f"デザイン: 現状{design}/5、競合標準3/5、提案後5/5",
        f"SEO: 現状{search}/5、競合標準3/5、提案後5/5",
        f"導線設計: 現状{conversion}/5、競合標準3/5、提案後5/5",
        f"コンテンツ量: 現状{content}/5、競合標準3/5、提案後4/5",
        f"更新性: 現状{cms}/5、競合標準3/5、提案後4/5",
        f"CTA: 現状{cta}/5、競合標準3/5、提案後5/5",
    ]


def _derive_winning_strategy(text: str) -> str:
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        return "物件検索で勝つ"
    if _contains_any(text, ["SEO", "検索", "自然検索", "流入"]):
        return "SEOで勝つ"
    if _contains_any(text, ["実績", "事例", "導入"]):
        return "実績訴求で勝つ"
    if _contains_any(text, ["問い合わせ", "問合せ", "CV", "CTA"]):
        return "検索導線で勝つ"
    return "実績訴求とCTA改善で勝つ"


def _derive_estimate_summary(payload: ProposalRequest, text: str) -> dict[str, Any]:
    page_count = _extract_page_count(payload.estimated_page_count, text)
    page_base = max(8, page_count)
    has_cms = _flag_enabled(payload.cms_required, text, ["CMS", "WordPress", "更新"])
    has_form = _flag_enabled(payload.contact_form_required, text, ["問い合わせフォーム", "問合せフォーム", "フォーム", "資料請求"])
    has_special = _flag_enabled(payload.special_function_required, text, ["物件検索", "検索機能", "会員", "予約", "決済", "特殊機能"])
    has_seo = _flag_enabled(payload.seo_required, text, ["SEO", "自然検索", "検索流入"])
    has_content = _flag_enabled(payload.content_creation_required, text, ["撮影", "原稿", "ライティング", "取材"])

    lines = [
        {"name": "要件整理・ディレクション", "min": 45 if page_count > 15 else 30, "max": 75 if page_count > 15 else 50, "priority": "必須対応", "enabled": True},
        {"name": "情報設計・ワイヤーフレーム", "min": 25 + page_base, "max": 45 + page_base * 2, "priority": "必須対応", "enabled": True},
        {"name": "デザイン制作", "min": 45 + page_base * 4, "max": 75 + page_base * 7, "priority": "必須対応", "enabled": True},
        {"name": "フロントエンド実装", "min": 50 + page_base * 5, "max": 85 + page_base * 8, "priority": "必須対応", "enabled": True},
        {"name": "CMS構築", "min": 50, "max": 90, "priority": "推奨対応", "enabled": has_cms},
        {"name": "フォーム実装", "min": 15, "max": 30, "priority": "必須対応", "enabled": has_form},
        {"name": "特殊機能開発", "min": 80, "max": 180, "priority": "オプション対応", "enabled": has_special},
        {"name": "SEO初期設計", "min": 20, "max": 40, "priority": "推奨対応", "enabled": has_seo},
        {"name": "撮影・原稿作成", "min": 30, "max": 80, "priority": "オプション対応", "enabled": has_content},
        {"name": "テスト・公開作業", "min": 20, "max": 35, "priority": "必須対応", "enabled": True},
        {"name": "運用保守", "min": 10, "max": 20, "priority": "オプション対応", "enabled": True},
    ]
    enabled_lines = [line for line in lines if line["enabled"]]
    total_min = sum(int(line["min"]) for line in enabled_lines)
    total_max = sum(int(line["max"]) for line in enabled_lines)
    budget = _extract_budget_amount(f"{payload.budget_range}\n{text}")
    if budget is None:
        budget_fit = "予算未入力"
    elif budget >= total_max:
        budget_fit = "予算内"
    elif budget >= total_min * 0.85:
        budget_fit = "やや調整必要"
    else:
        budget_fit = "予算超過の可能性あり"

    return {
        "page_count": page_count,
        "lines": lines,
        "total_min": total_min,
        "total_max": total_max,
        "total_label": f"{total_min}万〜{total_max}万円",
        "budget": budget,
        "budget_label": "未入力" if budget is None else f"{budget}万円",
        "budget_fit": budget_fit,
        "required": [line["name"] for line in enabled_lines if line["priority"] == "必須対応"],
        "recommended": [line["name"] for line in enabled_lines if line["priority"] == "推奨対応"],
        "optional": [line["name"] for line in enabled_lines if line["priority"] == "オプション対応"],
    }


def _extract_page_count(primary: str, text: str) -> int:
    for source in (primary, text):
        normalized = _normalize_number_text(source)
        match = re.search(r"(\d+)\s*(?:ページ|頁|p)", normalized, flags=re.IGNORECASE)
        if match:
            return max(1, min(60, int(match.group(1))))
        number = re.search(r"\d+", normalized)
        if source == primary and number:
            return max(1, min(60, int(number.group(0))))
    return 10


def _extract_budget_amount(text: str) -> int | None:
    normalized = _normalize_number_text(text)
    amounts = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(万円|万|円)", normalized):
        amount = float(match.group(1))
        amounts.append(round(amount / 10000) if match.group(2) == "円" else round(amount))
    return max(amounts) if amounts else None


def _normalize_number_text(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９，", "0123456789,")).replace(",", "")


def _flag_enabled(value: str, text: str, patterns: list[str]) -> bool:
    if _contains_any(value, ["なし", "不要", "無", "無し", "対象外"]):
        return False
    if _contains_any(value, ["あり", "有", "必要", "希望", "対象", "実施", "要"]):
        return True
    return _contains_any(text, patterns)


def _derive_target_users(text: str, concept: str) -> list[str]:
    if concept == "採用強化":
        return ["主要ターゲット: 応募を検討する求職者", "ニーズ: 仕事内容、働く環境、成長機会を知りたい", "不安: 社風や選考後の働き方が見えにくい", "必要コンテンツ: 社員紹介、募集要項、FAQ、応募導線"]
    if concept == "物件検索強化":
        return ["主要ターゲット: 条件に合う物件を探す検討者", "ニーズ: エリア、価格、条件で素早く比較したい", "不安: 問い合わせ後の流れや物件の詳細が不足する", "必要コンテンツ: 物件検索、詳細ページ、FAQ、内見予約"]
    if _contains_any(text, ["BtoB", "法人", "企業"]):
        return ["主要ターゲット: サービス導入を検討する法人担当者", "ニーズ: 自社課題に合う支援内容と実績を知りたい", "不安: 費用対効果や導入後の運用負荷を見極めたい", "必要コンテンツ: サービス詳細、事例、料金観点、問い合わせ導線"]
    return ["主要ターゲット: サービス比較中の見込み顧客", "ニーズ: 強み、実績、費用感を短時間で把握したい", "不安: 自社に合うか、依頼後の進め方が分かりにくい", "必要コンテンツ: サービス、実績、FAQ、問い合わせ"]


def _derive_content_plan(text: str, concept: str) -> list[str]:
    items = ["サービス詳細: 強み、対象課題、提供範囲を明確化", "実績・事例: 成果とプロセスを見せて比較検討を後押し", "FAQ: 費用、納期、運用、CMSの不安を先回りして解消", "お問い合わせ: CTAとフォーム項目を最短化"]
    if concept == "採用強化":
        items[0] = "採用情報: 募集職種、働き方、社員の声を整理"
    if _contains_any(text, ["資料請求", "ホワイトペーパー"]):
        items.append("資料ダウンロード: 検討初期のリード獲得導線を設置")
    return _unique_texts(items, 4)


def _derive_web_strategy(concept: str, needs: list[str]) -> list[str]:
    return _unique_texts(
        [
            f"戦略軸: {concept}",
            f"集客: {needs[0] if needs else '検索流入と指名流入'}を起点に入口を整備",
            "比較検討: サービス、実績、FAQで判断材料を増やす",
            "CV: CTAとフォームを整理し、問い合わせまでの迷いを減らす",
        ],
        4,
    )


def _build_mock_issues(payload: ProposalRequest, signals: dict[str, Any]) -> list[dict[str, str]]:
    brief_head = payload.project_brief.strip().replace("\n", " ")[:90]
    needs = list(signals["needs"])  # type: ignore[arg-type]
    issues: list[dict[str, str]] = []
    for need in needs[:3]:
        issues.append(
            {
                "issue": _issue_from_need(need),
                "background": f"案件概要から「{need}」を重要テーマとして扱います。",
                "evidence": f"案件概要の冒頭情報: {brief_head}",
                "confidence": "中。次回ヒアリングで根拠を補強します。",
            }
        )

    fallback_issues = [
        {
            "issue": "Webサイトの目的と優先KPIが十分に具体化されていない状態",
            "background": "制作範囲と改善したい成果指標を初回設計で明確にします。",
            "evidence": f"案件概要の冒頭情報: {brief_head}",
            "confidence": "中。次回ヒアリングで目的と指標を合意します。",
        },
        {
            "issue": "ターゲット別の導線や訴求が不足している状態",
            "background": "問い合わせ、採用、資料請求など複数目的がある場合、導線設計の優先順位が重要になります。",
            "evidence": "入力情報から、ユーザー行動の整理を提案価値として扱います。",
            "confidence": "中。アクセス解析と既存サイト確認で精度を高めます。",
        },
        {
            "issue": "公開後の運用改善体制が未整備な状態",
            "background": "Web制作は公開後の改善運用まで含めることで成果に結びつきやすくなります。",
            "evidence": "案件概要に運用体制の記載が少ない場合、提案時に補足すると有効です。",
            "confidence": "低から中。運用希望の有無を次回確認事項にします。",
        },
    ]
    existing = [issue["issue"] for issue in issues]
    for issue in fallback_issues:
        if len(issues) >= 3:
            break
        if not _is_same_text(issue["issue"], existing):
            issues.append(issue)
            existing.append(issue["issue"])
    return issues[:3]


def _mock_win_probability(signals: dict[str, Any]) -> dict[str, Any]:
    has_budget = bool(signals["has_budget"])
    has_deadline = bool(signals["has_deadline"])
    has_competitor = bool(signals.get("has_competitor"))
    budget_fit = str(signals.get("budget_fit", "予算未入力"))
    needs = list(signals["needs"])  # type: ignore[arg-type]
    confirmations = list(signals["confirmations"])  # type: ignore[arg-type]

    if has_budget and has_deadline and len(needs) >= 2 and has_competitor:
        rank = "A"
        label = "受注確率 80%｜条件が見えやすい案件"
        reason = "課題、予算、納期、競合比較の前提がそろっており、勝ち筋を明確にした提案へ具体化しやすい案件です。"
    elif has_budget or has_deadline or len(needs) >= 2:
        rank = "B"
        label = "受注確率 60%｜追加確認で上振れする案件"
        reason = "課題は見えています。予算、納期、決裁条件を詰めることで提案精度を高めます。"
    elif needs:
        rank = "C"
        label = "受注確率 40%｜条件整理を優先する案件"
        reason = "課題や条件の入力が少ないため、初回ヒアリングで目的、予算、決裁条件を見極めます。"
    else:
        rank = "D"
        label = "受注確率 20%｜商談化の見極めが先の案件"
        reason = "案件条件と顧客課題がまだ薄いため、初回接点では目的、予算、決裁者、競合状況を確認します。"

    probability = {"A": 80, "B": 60, "C": 40, "D": 20}[rank]
    if budget_fit == "予算内":
        probability = min(90, probability + 10)
    elif budget_fit == "やや調整必要":
        probability = max(20, probability - 5)
    elif budget_fit == "予算超過の可能性あり":
        probability = max(20, probability - 15)
    rank = _rank_from_probability(probability)
    suffix = {
        "A": "条件が見えやすい案件",
        "B": "追加確認で上振れする案件",
        "C": "条件整理を優先する案件",
        "D": "商談化の見極めが先の案件",
    }[rank]
    label = f"受注確率 {probability}%｜{suffix}"
    reason = f"{reason} 概算見積の予算適合は「{budget_fit}」です。"

    risk_factors = _unique_texts(
        [
            "" if has_budget else "予算未確定",
            "" if has_deadline else "納期未確認",
            "競合有り" if has_competitor else "競合未確認",
            "概算見積と予算感に調整が必要" if budget_fit == "やや調整必要" else "",
            "概算見積が予算を超える可能性がある" if budget_fit == "予算超過の可能性あり" else "",
            "決裁者未確認",
        ],
        4,
    )
    improvement_actions = _derive_improvement_actions(has_budget, has_deadline, has_competitor, budget_fit, confirmations)
    risk_score = _risk_score_for_probability(probability, len(risk_factors))
    projected_probability = _projected_probability(probability, risk_score, len(improvement_actions))

    return {
        "rank": rank,
        "probability": probability,
        "label": label,
        "reason": reason,
        "risk_score": risk_score,
        "risk_label": _risk_label(risk_score),
        "positive_factors": _unique_texts(
            [
                "Webサイト改善の目的が見え始めている",
                f"{needs[0]}に接続した提案ができる" if needs else "",
                "競合比較をもとに勝ち筋を提示できる" if has_competitor else "",
                "概算見積が予算感に収まる" if budget_fit == "予算内" else "",
                "自社サービス情報を制作方針に反映できる",
            ],
            3,
        ),
        "risk_factors": risk_factors,
        "recommended_next_actions": confirmations[:3],
        "improvement_actions": improvement_actions,
        "projected_probability_after_actions": projected_probability,
    }


def _rank_from_probability(probability: int) -> str:
    if probability >= 80:
        return "A"
    if probability >= 60:
        return "B"
    if probability >= 40:
        return "C"
    return "D"


def _risk_score_for_probability(probability: int, risk_count: int) -> int:
    if probability <= 25:
        score = 5
    elif probability <= 40:
        score = 4
    elif probability <= 60:
        score = 3
    elif probability <= 75:
        score = 2
    else:
        score = 1
    if risk_count >= 4:
        score = min(5, score + 1)
    return score


def _risk_label(score: int) -> str:
    normalized = max(1, min(5, score))
    return f"{'★' * normalized}{'☆' * (5 - normalized)}"


def _derive_improvement_actions(
    has_budget: bool,
    has_deadline: bool,
    has_competitor: bool,
    budget_fit: str,
    confirmations: list[str],
) -> list[str]:
    actions = [
        "決裁者確認",
        "予算確認" if not has_budget or budget_fit in {"やや調整必要", "予算超過の可能性あり"} else "",
        "競合ヒアリング" if not has_competitor else "競合比較条件確認",
        "納期確認" if not has_deadline else "",
    ]
    for item in confirmations:
        if "CMS" in item:
            actions.append("CMS要件確認")
        elif "SEO" in item:
            actions.append("SEO要件確認")
        elif "運用" in item:
            actions.append("運用範囲確認")
    return _unique_texts(actions, 3)


def _projected_probability(probability: int, risk_score: int, action_count: int) -> int:
    if probability <= 25:
        uplift = 25
    elif probability <= 40:
        uplift = 20
    elif probability <= 60:
        uplift = 15
    else:
        uplift = 10
    if risk_score <= 2:
        uplift = min(uplift, 10)
    if action_count < 3:
        uplift = max(8, uplift - 5)
    return min(90, probability + uplift)


def _issue_from_need(need: str) -> str:
    if "問い合わせ" in need:
        return "問い合わせにつながる導線やCTAが弱い状態"
    if "採用" in need:
        return "採用候補者に向けた情報整理が不足している状態"
    if "リニューアル" in need:
        return "現行サイトの情報鮮度や構成が現状に合っていない状態"
    if "CMS" in need:
        return "更新しやすいCMS・運用設計が未整備な状態"
    if "SEO" in need:
        return "SEOを見据えた情報設計やコンテンツ設計が不足している状態"
    if "運用" in need:
        return "公開後の運用保守・改善サイクルが未整備な状態"
    return "Webサイトの役割と優先課題が具体化されていない状態"


def _build_confirmation_items(full_text: str) -> list[str]:
    has_budget_detail = "予算" in full_text and not _contains_any(full_text, ["予算は未定", "予算未定", "予算感未定"])
    confirmations = [
        "予算感・上限・見積の出し方" if not has_budget_detail else "予算に合わせた必須範囲とオプション",
        "希望公開時期・社内確認フロー" if not _contains_any(full_text, ["納期", "公開時期", "公開希望", "リリース希望", "早め", "急ぎ"]) else "希望納期に対する素材準備と確認体制",
        "CMS導入・更新権限・更新頻度" if not _contains_any(full_text, ["CMS", "更新"]) else "CMS要件と更新担当範囲",
        "SEO・コンテンツ改善の必要性" if not _contains_any(full_text, ["SEO", "検索"]) else "SEO対象キーワードと既存流入状況",
        "公開後の運用保守範囲" if not _contains_any(full_text, ["運用", "保守", "改善"]) else "公開後改善のレポート頻度と支援範囲",
    ]
    return _unique_texts(confirmations, 5)


def _extract_text_items(text: str, max_count: int) -> list[str]:
    if not text.strip():
        return []
    parts = []
    for line in re.split(r"[\n。;；]+", text):
        item = re.sub(r"^[・•\-\d\s.．、]+", "", line.strip())
        if item:
            parts.append(_shorten(item, 48))
    return _unique_texts(parts, max_count)


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _unique_texts(items: list[str], max_count: int) -> list[str]:
    unique: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or _is_same_text(cleaned, unique):
            continue
        unique.append(cleaned)
        if len(unique) >= max_count:
            break
    return unique


def _is_same_text(value: str, existing: list[str]) -> bool:
    key = _normalize_text(value)
    return any(key == _normalize_text(item) for item in existing)


def _normalize_text(value: str) -> str:
    return re.sub(r"[\s　・•\-ー、。,.．:：/／「」『』（）()\[\]]+", "", value.lower())


def _shorten(value: str, max_length: int) -> str:
    cleaned = value.strip().replace("\n", " ")
    return cleaned if len(cleaned) <= max_length else f"{cleaned[: max_length - 1]}…"


def _join_for_sentence(items: list[str] | object) -> str:
    if not isinstance(items, list) or not items:
        return "確認事項"
    return "、".join(items[:3])


def _build_mock_analysis(payload: ProposalRequest) -> ProposalAnalysis:
    client_name = _guess_client_name(payload.client_company_info)
    brief_head = payload.project_brief.strip().replace("\n", " ")[:90]
    signals = _extract_input_signals(payload)
    issues = _build_mock_issues(payload, signals)

    slides = []
    for index, section in enumerate(BASIC_PROPOSAL_STRUCTURE, start=1):
        slides.append(
            {
                "slide_no": index,
                "section": section,
                "title": _mock_slide_title(section),
                "body": _mock_slide_body(section, payload, issues, signals),
                "speaker_notes": _mock_speaker_notes(section),
                "visual_suggestion": _mock_visual(section),
            }
        )

    win_probability = _mock_win_probability(signals)

    data = {
        "project_summary": (
            f"本案件は、{client_name}向けにReady Crewの案件概要をもとにWebサイト制作または改善提案の初稿を作成するものです。"
            f"案件概要の「{brief_head}」を起点に、現状理解、競合比較、ターゲット、Web戦略、KPI、制作方針までを一貫して設計します。"
        ),
        "assumed_customer_issues": issues,
        "issue_priorities": [
            {
                "rank": 1,
                "issue": issues[0]["issue"],
                "reason": "提案全体の軸になり、スコープと成果指標の合意に直結するためです。",
                "proposed_response": "初回ヒアリングで目的、KPI、優先ターゲット、必要ページを整理する提案にします。",
            },
            {
                "rank": 2,
                "issue": issues[1]["issue"],
                "reason": "サイト構成、コンテンツ、CTA設計に影響するためです。",
                "proposed_response": "ターゲット別の情報設計と主要導線の改善を制作方針に含めます。",
            },
            {
                "rank": 3,
                "issue": issues[2]["issue"],
                "reason": "公開後の成果改善に関わるものの、MVP提案では確認後に段階化しやすいためです。",
                "proposed_response": "月次改善、アクセス解析、更新支援をオプション提案として整理します。",
            },
        ],
        "win_probability": win_probability,
        "proposal_policy": (
            f"顧客理解を起点に、{_join_for_sentence(signals['needs'])}を中心課題として整理し、"
            f"{signals['concept']}を提案コンセプトに据えます。"
            "Webサイトの役割、制作範囲、公開後の改善方針を一貫して示します。"
            f"次回は{_join_for_sentence(signals['confirmations'])}を確認し、見積とスケジュールの精度を高めます。"
        ),
        "proposal_story": (
            "まず提案サマリーで全体像を示し、現状理解と想定課題で提案の前提を揃えます。"
            "次に、市場・競合分析、ターゲット分析、カスタマージャーニーからWeb戦略、サイトマップ、コンテンツ設計へ落とし込みます。"
            "最後にKPI、制作方針、スケジュール、体制、費用、今後の進め方を提示し、実行判断につなげます。"
        ),
        "proposal_structure": [
            {
                "section": section,
                "objective": _mock_section_objective(section),
                "key_message": _mock_section_key_message(section),
            }
            for section in BASIC_PROPOSAL_STRUCTURE
        ],
        "slide_scripts": slides,
        "expected_questions_and_answers": [
            {
                "question": "費用はどの程度変動しますか。",
                "answer": "ページ数、原稿作成範囲、撮影やシステム連携の有無で変動します。初回ヒアリング後に優先度を合意し、必須範囲とオプションを分けて提示します。",
            },
            {
                "question": "公開後の運用も依頼できますか。",
                "answer": "アクセス解析、改善提案、軽微な更新、コンテンツ追加を月次支援として設計します。必要な支援範囲は現行体制を確認し、体制紹介と費用概算へ反映します。",
            },
            {
                "question": "他社と比較した強みは何ですか。",
                "answer": f"単なる制作ではなく、課題整理、情報設計、公開後の改善まで一貫して提案します。入力された自社サービス情報では、{_join_for_sentence(signals['services'])}を差別化材料として提示します。",
            },
        ],
        "quality_check": {
            "logical_consistency": "提案ストーリーは、現状理解、提案方針、KPI、制作方針の順で整合しています。最終提出前に固有名詞を照合してください。",
            "typos": "表記ゆれと固有名詞を最終チェック項目として残します。",
            "proposal_coverage": "提案サマリー、現状理解、競合分析、ターゲット分析、ジャーニー、Web戦略、サイトマップ、コンテンツ、KPI、体制、費用まで網羅しています。",
            "competitive_differentiation": "課題整理から公開後改善までつなげる点を差別化材料として提示しています。自社独自プロセスと実績でさらに補強できます。",
            "alignment_with_customer_issues": "案件概要から抽出した課題と、解決策、制作方針、KPIが対応しています。",
            "human_review_notes": f"次回確認事項: {_join_for_sentence(signals['confirmations'])}",
        },
        "powerpoint_generation_data": {
            "deck_title": f"{client_name} Webサイト制作ご提案書",
            "client_name": client_name,
            "slides": [
                {
                    "slide_no": slide["slide_no"],
                    "layout": "title" if slide["slide_no"] == 1 else "content",
                    "title": slide["title"],
                    "bullets": slide["body"],
                    "speaker_notes": slide["speaker_notes"],
                    "visual_suggestion": slide["visual_suggestion"],
                }
                for slide in slides
            ],
        },
    }

    return ProposalAnalysis.model_validate(data)


def _guess_client_name(client_company_info: str) -> str:
    if not client_company_info.strip():
        return "提案先企業"
    for line in client_company_info.strip().splitlines():
        candidate = re.sub(r"^(企業名|会社名|提案先企業名|提案先企業|提案先|顧客名|クライアント)\s*[:：]\s*", "", line.strip())
        candidate = candidate.strip(" ・-　")
        generic_names = {"提案先企業", "提案先企業情報", "企業情報", "会社情報", "未入力"}
        if candidate and _normalize_text(candidate) not in {_normalize_text(name) for name in generic_names}:
            return candidate[:40]
    return "提案先企業"


def _mock_slide_title(section: str) -> str:
    titles = {
        "表紙": "Webサイト制作ご提案書",
        "提案サマリー": "提案サマリー",
        "現状理解": "現状理解",
        "想定される課題": "想定される課題",
        "市場・競合分析": "市場・競合分析",
        "競合比較分析": "競合比較分析",
        "ターゲットユーザー分析": "ターゲットユーザー分析",
        "カスタマージャーニー": "カスタマージャーニー",
        "Web戦略": "Web戦略",
        "サイトマップ": "サイトマップ",
        "コンテンツ設計": "コンテンツ設計",
        "KPI設計": "KPI設計",
        "制作方針": "制作方針",
        "スケジュール": "想定スケジュール",
        "体制": "プロジェクト体制",
        "費用概算": "費用概算",
        "概算見積": "概算見積",
        "予算適合判定": "予算適合判定",
        "必須・推奨・オプション対応": "必須・推奨・オプション対応",
        "今後の進め方": "今後の進め方",
    }
    return titles.get(section, section)


def _mock_slide_body(
    section: str,
    payload: ProposalRequest,
    issues: list[dict[str, str]],
    signals: dict[str, Any],
) -> list[str]:
    client_name = _guess_client_name(payload.client_company_info)
    needs = list(signals["needs"])  # type: ignore[arg-type]
    services = list(signals["services"])  # type: ignore[arg-type]
    cases = list(signals["cases"])  # type: ignore[arg-type]
    confirmations = list(signals["confirmations"])  # type: ignore[arg-type]
    template_sections = list(signals["template_sections"])  # type: ignore[arg-type]
    journey = list(signals["journey"])
    sitemap = list(signals["sitemap"])
    kpi = list(signals["kpi"])
    competitor = list(signals["competitor"])
    winning_strategy = str(signals["winning_strategy"])
    targets = list(signals["targets"])
    content = list(signals["content"])
    web_strategy = list(signals["web_strategy"])
    estimate = signals["estimate"]
    estimate_lines = [
        f"{line['name']}: {line['min']}万〜{line['max']}万円" if line["enabled"] else f"{line['name']}: 対象外"
        for line in estimate["lines"]
    ]

    bodies = {
        "表紙": [f"{client_name}様向けのWebサイト制作提案", f"提案コンセプト: {signals['concept']}", "成果につながるWebサイト改善提案"],
        "提案サマリー": _unique_texts(
            [
                f"提案コンセプト: {signals['concept']}",
                f"解決する課題: {_join_for_sentence(needs)}",
                "主要施策: 情報設計、導線改善、CMS/SEO、コンテンツ強化を一体で実施",
                f"期待成果: {', '.join(kpi[:2])}",
            ],
            4,
        ),
        "現状理解": _unique_texts(
            [
                f"現状: {signals['current_state']}",
                f"課題: {signals['business_issue']}",
                f"機会: {signals['opportunity']}",
                f"目指す状態: {signals['target_state']}",
            ],
            4,
        ),
        "想定される課題": [issue["issue"] for issue in issues[:4]],
        "市場・競合分析": competitor,
        "競合比較分析": _unique_texts(
            [
                f"勝ち筋: {winning_strategy}",
                *competitor,
                "競合比較の観点をもとに、提案内で優先する改善ポイントを明確化",
            ],
            4,
        ),
        "ターゲットユーザー分析": targets,
        "カスタマージャーニー": journey,
        "Web戦略": web_strategy,
        "サイトマップ": [f"トップ > {' / '.join(sitemap[1:6])}", "サービス・実績から問い合わせへつながる導線を設計", "お知らせと実績をCMS更新領域として配置"],
        "コンテンツ設計": content,
        "KPI設計": kpi,
        "制作方針": _unique_texts(services + ["初期設計を重視した制作プロセス", "確認しやすいワイヤーフレーム作成"], 4),
        "スケジュール": _unique_texts(
            [
                "要件整理・優先順位決定",
                "設計・デザイン確認",
                "実装・CMS設定・検証" if bool(signals["has_cms"]) else "実装・検証",
                "公開・運用改善" if bool(signals["has_operation"]) else "公開準備",
            ],
            4,
        ),
        "体制": _unique_texts(
            [
                "ディレクターを中心に進行管理",
                "デザイナー・エンジニアが連携",
                "CMS・運用支援まで対応" if bool(signals["has_cms"]) or bool(signals["has_operation"]) else "公開後の軽微な更新相談に対応",
                "定例確認で認識齟齬を抑制",
            ],
            4,
        ),
        "費用概算": _unique_texts(
            [
                f"合計概算: {estimate['total_label']}",
                f"予算適合: {estimate['budget_fit']}（予算感: {estimate['budget_label']}）",
                "必須範囲とオプションを分離",
                "予算に合わせて優先順位を調整" if bool(signals["has_budget"]) else "予算感を次回確認事項として概算を精緻化",
                f"想定ページ数: {estimate['page_count']}ページ",
            ],
            4,
        ),
        "概算見積": _unique_texts(
            [*estimate_lines, f"合計概算: {estimate['total_label']}"],
            4,
        ),
        "予算適合判定": _unique_texts(
            [
                f"判定: {estimate['budget_fit']}",
                f"入力予算: {estimate['budget_label']}",
                f"概算見積: {estimate['total_label']}",
                "予算内に収める場合は必須対応を優先し、特殊機能や撮影・原稿作成を段階提案にする",
            ],
            4,
        ),
        "必須・推奨・オプション対応": _unique_texts(
            [
                f"必須対応: {_join_for_sentence(estimate['required'])}",
                f"推奨対応: {_join_for_sentence(estimate['recommended'])}",
                f"オプション対応: {_join_for_sentence(estimate['optional'])}",
                "予算と納期に応じて、推奨・オプションを段階的に追加",
            ],
            4,
        ),
        "今後の進め方": _unique_texts(
            [
                "初回打ち合わせで目的、KPI、優先範囲を合意",
                "素材、原稿、既存サイト情報を確認",
                f"次回確認事項: {_join_for_sentence(confirmations)}",
                f"過去提案書テンプレートの構成: {_join_for_sentence(template_sections)}" if template_sections else "",
            ],
            4,
        ),
    }
    return bodies.get(section, ["次回確認事項を整理します"])


def _solution_copy(issue: str) -> str:
    if "問い合わせ" in issue:
        return "主要CTAと問い合わせ導線を再設計"
    if "採用" in issue:
        return "採用候補者向け情報と応募導線を整理"
    if "情報鮮度" in issue or "現行サイト" in issue:
        return "情報設計とサービス訴求を再構成"
    if "CMS" in issue:
        return "CMS要件と更新運用フローを設計"
    if "SEO" in issue:
        return "SEOを見据えたサイト構造とコンテンツを整理"
    if "運用" in issue:
        return "公開後の改善サイクルを提案に含める"
    return "要件整理を通じて優先度を明確化"


def _mock_speaker_notes(section: str) -> str:
    return f"{section}について、現時点では仮説として整理していることを伝え、詳細ヒアリングで精度を高める前提を補足します。"


def _mock_visual(section: str) -> str:
    visuals = {
        "表紙": "フルビジュアル表紙、提案先名、提案コンセプト",
        "提案サマリー": "提案価値を3点で整理したサマリーカード",
        "現状理解": "現状、課題、機会、目指す状態の4象限カード",
        "想定される課題": "課題を優先度順に並べたカード",
        "市場・競合分析": "5段階評価の競合比較表",
        "競合比較分析": "比較ポイントと勝ち筋を整理した競合分析表",
        "ターゲットユーザー分析": "ターゲット、ニーズ、不安、必要コンテンツのカード",
        "カスタマージャーニー": "認知、比較検討、問い合わせの横並びフロー",
        "Web戦略": "集客、比較検討、CV、運用改善の戦略カード",
        "サイトマップ": "TOPから主要ページへ展開するサイトツリー",
        "コンテンツ設計": "コンテンツ群と役割を示すカード",
        "KPI設計": "数値目標のKPIグラフ",
        "制作方針": "制作プロセス図",
        "スケジュール": "週次ガントチャート",
        "体制": "役割別の体制図",
        "費用概算": "必須範囲とオプションの表",
        "概算見積": "見積内訳と合計レンジの表",
        "予算適合判定": "予算感と概算見積を比較する判定カード",
        "必須・推奨・オプション対応": "対応範囲の優先順位を3列で整理",
        "今後の進め方": "次回アクションのタイムライン",
    }
    return visuals.get(section, "提案内容を補足する図表")


def _mock_section_objective(section: str) -> str:
    objectives = {
        "表紙": "提案書の前提と対象を示す",
        "提案サマリー": "提案全体の価値と実施範囲を短時間で伝える",
        "現状理解": "案件概要から読み取れる現状、課題、機会、目指す状態を共有する",
        "想定される課題": "優先して解決すべき課題を絞り込む",
        "市場・競合分析": "競合と比較した改善余地を可視化する",
        "競合比較分析": "競合サイトとの差分から提案の勝ち筋を定義する",
        "ターゲットユーザー分析": "誰に何を伝えるべきかを定義する",
        "カスタマージャーニー": "ユーザー行動と改善接点を可視化する",
        "Web戦略": "成果につながるWeb活用方針を示す",
        "サイトマップ": "運用しやすく成果につながるサイト構成を示す",
        "コンテンツ設計": "必要コンテンツと役割を定義する",
        "KPI設計": "成果判断に使う指標と目標を提示する",
        "制作方針": "制作の進め方と品質担保の考え方を示す",
        "スケジュール": "プロジェクトの進行イメージを共有する",
        "体制": "安心して依頼できる進行体制を示す",
        "費用概算": "予算検討の土台を提示する",
        "概算見積": "制作範囲ごとの金額レンジを提示する",
        "予算適合判定": "予算感と概算見積の差分を判断し、調整方針を示す",
        "必須・推奨・オプション対応": "予算内で優先すべき対応範囲を分類する",
        "今後の進め方": "次回アクションと意思決定ポイントを示す",
    }
    return objectives.get(section, "提案内容を整理する")


def _mock_section_key_message(section: str) -> str:
    messages = {
        "表紙": "案件概要をもとに、成果につながるWebサイト制作方針を提案します。",
        "提案サマリー": "戦略、設計、制作、運用を一体化し、Webサイトを成果創出の基盤にします。",
        "現状理解": "現状、課題、機会、目指す状態を揃え、提案の前提を明確にします。",
        "想定される課題": "成果に直結する課題を優先度順に解決します。",
        "市場・競合分析": "競合標準を超える設計品質と問い合わせ導線を実装します。",
        "競合比較分析": "競合比較から勝ち筋を明確化し、提案の差別化ポイントとして示します。",
        "ターゲットユーザー分析": "ターゲットの不安を解消し、問い合わせ判断を後押しします。",
        "カスタマージャーニー": "認知から問い合わせまでの流れを改善し、成果導線を強化します。",
        "Web戦略": "集客、比較検討、CV、運用をつなげたWeb戦略を実行します。",
        "サイトマップ": "更新しやすく、問い合わせにつながるサイト構成を提案します。",
        "コンテンツ設計": "サービス、実績、FAQ、フォームを成果導線として設計します。",
        "KPI設計": "問い合わせ数、CV率、自然検索流入、資料DL数を目標化します。",
        "制作方針": "確認しやすく、公開後も改善しやすい制作を進めます。",
        "スケジュール": "要件整理から公開まで段階的に進行します。",
        "体制": "進行管理と専門職の連携により品質を担保します。",
        "費用概算": "スコープに応じて必須範囲とオプションを分けます。",
        "概算見積": "案件条件から概算見積レンジを提示し、費用判断の土台を作ります。",
        "予算適合判定": "予算感とのズレを明確にし、調整すべき範囲を提示します。",
        "必須・推奨・オプション対応": "予算内で成果を出すため、対応範囲の優先順位を明確にします。",
        "今後の進め方": "次回確認事項を合意し、制作開始に向けた準備を進めます。",
    }
    return messages.get(section, "次回確認事項を整理します。")

