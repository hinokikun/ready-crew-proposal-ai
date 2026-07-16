from __future__ import annotations

from datetime import date
import re

from app.models import PowerPointData, PowerPointSlide, PptxDownloadRequest
from app.proposal_profiles import ProposalProfile, get_proposal_profile, proposal_profile_for_text, score_rows_for_axes
from app.services.pptx_theme import COLORS
from app.services.pptx_parts.models import EstimateSummary


def _split_label_body(value: str) -> tuple[str, str]:
    if ":" in value:
        label, body = value.split(":", 1)
        return label.strip(), body.strip()
    if "：" in value:
        label, body = value.split("：", 1)
        return label.strip(), body.strip()
    return value.strip(), value.strip()


def _profile_for_concept(concept: str) -> ProposalProfile:
    mapping = {
        "AI-OCR業務自動化": "ai_ocr",
        "定型業務自動化": "rpa",
        "営業情報の一元管理": "crm_sfa",
        "入力案件の業務改善": "other",
    }
    if concept in mapping:
        return get_proposal_profile(mapping[concept])
    if any(keyword in concept for keyword in ["Web", "CMS", "SEO", "CTA", "CV", "サイト"]):
        return get_proposal_profile("web")
    return get_proposal_profile("other")


def _fallback_slide(data: PowerPointData) -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=1,
        layout="title",
        title=data.deck_title or "業務改善ご提案書",
        bullets=[data.client_name or "提案先企業", "提案構成の生成結果をスライド化"],
        speaker_notes="生成結果をもとにした提案資料です。",
        visual_suggestion="表紙背景、企業名、自社ロゴ",
    )


def derive_concept(text: str) -> str:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.concept
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


def derive_current_understanding(project_brief: str, concept: str) -> dict[str, str]:
    profile = proposal_profile_for_text(project_brief)
    if profile.category != "web":
        points = extract_project_points(project_brief)
        issue = points[0] if points else profile.needs[0]
        return {
            "現状": f"{profile.label}の導入目的、対象業務、運用条件を整理する局面です。",
            "課題": issue,
            "機会": profile.summary,
            "目指す状態": f"{profile.concept}を軸に、導入範囲、効果測定、運用定着までを明確にします。",
        }

    points = extract_project_points(project_brief)
    current = "Webサイトの役割を見直し、営業・採用・広報の成果接点として再設計する局面です。"
    if _contains_any(project_brief, ["古", "リニューアル", "刷新", "改修"]):
        current = "現行サイトの情報鮮度と見せ方が、現在の事業内容や営業活動に追いついていない状態です。"
    elif _contains_any(project_brief, ["新規", "立ち上げ", "初めて"]):
        current = "新しいWeb接点を立ち上げ、事業内容と強みを伝える土台を作る局面です。"
    elif _contains_any(project_brief, ["問い合わせ", "問合せ", "CV"]):
        current = "Webサイトを問い合わせ獲得の接点として強化する段階です。"

    issue = points[0] if points else "Webサイトの目的と優先ターゲットの明確化"
    opportunity = concept_statement(concept)
    target = f"{concept}を軸に、訪問者が理解、比較、問い合わせまで迷わず進める状態を作ります。"
    return {"現状": current, "課題": issue, "機会": opportunity, "目指す状態": target}


def merge_understanding_items(base: dict[str, str], bullets: list[str]) -> dict[str, str]:
    merged = dict(base)
    for bullet in bullets:
        match = re.match(r"^(現状|課題|機会|目指す状態)\s*[:：]\s*(.+)$", bullet.strip())
        if match:
            merged[match.group(1)] = match.group(2)
    return merged


def concept_statement(concept: str) -> str:
    statements = {
        "AI-OCR業務自動化": "帳票読み取り、項目抽出、連携、例外処理を整え、手入力と確認作業を削減します。",
        "定型業務自動化": "対象業務、手順、例外処理を標準化し、RPAで安定した自動化を進めます。",
        "営業情報の一元管理": "顧客、商談、活動履歴を統合し、営業活動を見える化します。",
        "入力案件の業務改善": "案件目的、導入範囲、効果測定、運用定着を整理し、実行しやすい提案にします。",
        "問い合わせ最大化": "導線、CTA、実績訴求を連動させ、商談につながる問い合わせを増やします。",
        "採用強化": "仕事内容、働く魅力、応募導線を整理し、候補者の理解と応募行動を促します。",
        "ブランディング強化": "強み、実績、メッセージを統一し、第一印象と信頼感を高めます。",
        "物件検索強化": "検索導線と物件情報を整理し、比較検討から問い合わせまでを短縮します。",
        "検索流入強化": "検索意図に合う構造とコンテンツを設計し、自然検索からの流入を伸ばします。",
        "CMS運用強化": "更新しやすいCMSと運用フローを整備し、情報鮮度を維持します。",
        "Web成果最大化": "情報設計、導線、運用を整え、Webサイトを成果創出の基盤にします。",
    }
    return statements.get(concept, "案件目的、導入範囲、効果測定、運用定着を整理し、実行しやすい提案にします。")


def derive_journey_points(concept: str) -> list[tuple[str, str]]:
    profile = _profile_for_concept(concept)
    if profile.category != "web":
        return [_split_label_body(item) for item in profile.journey[:4]]
    if concept == "採用強化":
        return [("認知", "企業の魅力と募集職種を伝える"), ("比較検討", "働き方・社員情報・制度で納得感を高める"), ("問い合わせ", "応募フォームまでの導線を短くする")]
    if concept == "物件検索強化":
        return [("認知", "エリア・物件情報への入口を増やす"), ("比較検討", "条件検索と物件詳細で比較しやすくする"), ("問い合わせ", "内見予約・資料請求へ迷わず進める")]
    if concept == "ブランディング強化":
        return [("認知", "企業の強みと世界観を第一印象で伝える"), ("比較検討", "実績・サービス・選ばれる理由を深く見せる"), ("問い合わせ", "相談テーマ別に導線を分ける")]
    return [("認知", "SEO・広告・紹介からの受け皿を整える"), ("比較検討", "サービス内容・実績・FAQで不安を減らす"), ("問い合わせ", "CTAとフォーム導線を最短化する")]


def journey_action(stage: str, concept: str) -> str:
    profile = _profile_for_concept(concept)
    if profile.category != "web":
        return {
            "受付": "対象データと入力経路を整理",
            "抽出": "処理ルールと品質基準を設計",
            "確認": "例外処理と人手確認を明確化",
            "連携": "既存システムへの接続条件を整理",
            "現状把握": "対象業務と課題を棚卸し",
            "設計": "導入範囲と実行手順を定義",
            "導入": "小さく検証して拡張",
            "定着": "効果測定と改善を継続",
        }.get(stage, "導入後の運用改善につなげる")
    if stage == "認知":
        return "入口ページと訴求メッセージを最適化"
    if stage == "比較検討":
        return "実績、FAQ、料金観点で不安を解消"
    if concept == "採用強化":
        return "応募導線とフォーム到達を改善"
    if concept == "物件検索強化":
        return "内見予約と資料請求を促進"
    return "問い合わせCTAとフォーム導線を改善"


def derive_sitemap_items(text: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.structure_items
    items = ["トップ", "会社案内", "サービス", "実績", "お知らせ", "お問い合わせ"]
    if _contains_any(text, ["採用", "求人", "応募"]):
        items.insert(-1, "採用情報")
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        items.insert(2, "物件検索")
    if _contains_any(text, ["CMS", "FAQ", "よくある質問"]):
        items.insert(-1, "FAQ")
    if _contains_any(text, ["資料請求", "ホワイトペーパー"]):
        items.insert(-1, "資料ダウンロード")
    return unique_items(items, 9)


def sitemap_note(item: str) -> str:
    generic_notes = {
        "対象帳票": "処理対象を明確化",
        "入力経路": "取り込み方法を整理",
        "抽出項目": "必要データを定義",
        "確認画面": "例外確認を効率化",
        "CSV/API連携": "既存業務へ接続",
        "例外処理": "運用品質を担保",
        "運用レポート": "改善状況を可視化",
        "対象業務": "提案範囲を明確化",
        "課題": "優先論点を整理",
        "導入範囲": "段階導入を設計",
        "連携先": "既存システム条件",
        "運用体制": "定着に必要な役割",
        "効果測定": "KPI確認の土台",
    }
    if item in generic_notes:
        return generic_notes[item]
    if item == "サービス":
        return "提供価値と選ばれる理由"
    if item == "実績":
        return "比較検討を後押し"
    if item == "お知らせ":
        return "CMS更新の中心領域"
    if item == "FAQ":
        return "問い合わせ前の不安を解消"
    if item == "お問い合わせ":
        return "CV導線の最終接点"
    if item == "採用情報":
        return "候補者向け情報を集約"
    if item == "物件検索":
        return "条件検索と詳細導線"
    return "基本情報を整理"


def derive_kpi_rows(text: str, concept: str) -> list[tuple[str, str]]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return [_split_label_body(item) for item in profile.kpis[:4]]
    targets = derive_kpi_targets(text, concept)
    if concept == "採用強化":
        return [("問い合わせ数", f"月{int(targets['inquiries'])}件"), ("CV率", f"{targets['cv_rate']}%"), ("自然検索流入", f"月{int(targets['organic'])}セッション"), ("資料DL数", f"月{int(targets['downloads'])}件")]
    if concept == "物件検索強化":
        return [("問い合わせ数", f"月{int(targets['inquiries'])}件"), ("CV率", f"{targets['cv_rate']}%"), ("自然検索流入", f"月{int(targets['organic'])}セッション"), ("資料DL数", f"月{int(targets['downloads'])}件")]
    return [("問い合わせ数", f"月{int(targets['inquiries'])}件"), ("CV率", f"{targets['cv_rate']}%"), ("自然検索流入", f"月{int(targets['organic'])}セッション"), ("資料DL数", f"月{int(targets['downloads'])}件")]


def derive_kpi_targets(text: str, concept: str) -> dict[str, float]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return {"inquiries": 18, "cv_rate": 3.0, "organic": 3200, "downloads": 20}
    if concept == "採用強化":
        return {"inquiries": 8, "cv_rate": 2.0, "organic": 2500, "downloads": 10}
    if concept == "物件検索強化":
        return {"inquiries": 25, "cv_rate": 3.0, "organic": 4000, "downloads": 20}
    if _contains_any(text, ["SEO", "検索", "流入"]):
        return {"inquiries": 18, "cv_rate": 2.5, "organic": 5000, "downloads": 30}
    if _contains_any(text, ["問い合わせ", "問合せ", "CV"]):
        return {"inquiries": 20, "cv_rate": 2.8, "organic": 3500, "downloads": 25}
    return {"inquiries": 12, "cv_rate": 2.0, "organic": 2500, "downloads": 15}


def derive_competitor_rows(text: str) -> list[list[str]]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return score_rows_for_axes(profile.competitor_axes, text)
    scores = {
        "デザイン": 2 if _contains_any(text, ["古", "リニューアル", "刷新", "改修", "ブランド", "信頼感"]) else 3,
        "SEO": 2 if _contains_any(text, ["SEO", "検索", "自然検索", "流入"]) else 3,
        "導線設計": 2 if _contains_any(text, ["問い合わせ", "問合せ", "CV", "資料請求", "導線"]) else 3,
        "コンテンツ量": 2 if _contains_any(text, ["情報不足", "実績", "事例", "FAQ", "コンテンツ"]) else 3,
        "更新性": 2 if _contains_any(text, ["CMS", "更新", "運用", "お知らせ"]) else 3,
        "CTA": 2 if _contains_any(text, ["CTA", "問い合わせ", "問合せ", "CV", "フォーム"]) else 3,
    }
    high_priority = {"デザイン", "SEO", "導線設計", "CTA"}
    return [[key, score_label(value), score_label(3), score_label(5 if key in high_priority else 4)] for key, value in scores.items()]


def derive_winning_strategy(text: str) -> str:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.winning_strategy
    if _contains_any(text, ["物件", "不動産", "賃貸", "売買"]):
        return "物件検索で勝つ"
    if _contains_any(text, ["SEO", "検索", "自然検索", "流入"]):
        return "SEOで勝つ"
    if _contains_any(text, ["実績", "事例", "導入", "信頼"]):
        return "実績訴求で勝つ"
    if _contains_any(text, ["問い合わせ", "問合せ", "CV", "CTA", "フォーム"]):
        return "検索導線で勝つ"
    return "実績訴求とCTA改善で勝つ"


def has_competitor_context(context: PptxContext) -> bool:
    return bool(context.competitor_site_url or context.competitor_company_name)


def derive_target_user_rows(text: str, concept: str) -> list[tuple[str, str]]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return [_split_label_body(item) for item in profile.targets[:4]]
    if concept == "採用強化":
        return [("主要ターゲット", "応募を検討する求職者"), ("ニーズ", "仕事内容、働く環境、成長機会を知りたい"), ("不安", "社風や選考後の働き方が見えにくい"), ("必要コンテンツ", "社員紹介、募集要項、FAQ、応募導線")]
    if concept == "物件検索強化":
        return [("主要ターゲット", "条件に合う物件を探す検討者"), ("ニーズ", "エリア、価格、条件で素早く比較したい"), ("不安", "問い合わせ後の流れや物件詳細が不足する"), ("必要コンテンツ", "物件検索、詳細ページ、FAQ、内見予約")]
    if _contains_any(text, ["BtoB", "法人", "企業"]):
        return [("主要ターゲット", "サービス導入を検討する法人担当者"), ("ニーズ", "支援内容、実績、費用対効果を把握したい"), ("不安", "導入後の運用負荷と成果が見えにくい"), ("必要コンテンツ", "サービス詳細、事例、料金観点、問い合わせ")]
    return [("主要ターゲット", "サービス比較中の見込み顧客"), ("ニーズ", "強み、実績、費用感を短時間で把握したい"), ("不安", "自社に合うか、依頼後の進め方が分かりにくい"), ("必要コンテンツ", "サービス、実績、FAQ、問い合わせ")]


def derive_content_items(text: str, concept: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.content_items[:4]
    items = ["サービス詳細: 強み、対象課題、提供範囲を明確化", "実績・事例: 成果とプロセスを見せて比較検討を後押し", "FAQ: 費用、納期、運用、CMSの不安を先回りして解消", "お問い合わせ: CTAとフォーム項目を最短化"]
    if concept == "採用強化":
        items[0] = "採用情報: 募集職種、働き方、社員の声を整理"
    if _contains_any(text, ["資料請求", "ホワイトペーパー"]):
        items.append("資料ダウンロード: 検討初期のリード獲得導線を設置")
    return unique_items(items, 4)


def derive_web_strategy_items(text: str, concept: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.strategy_items[:4]
    return unique_items(
        [
            "集客: SEO・広告・紹介流入の受け皿を整備",
            "比較検討: サービス、実績、FAQで判断材料を提供",
            "問い合わせ: CTAとフォーム導線を短く設計",
            "運用改善: CMS更新とアクセス解析で継続改善",
        ],
        4,
    )


def score_label(value: int) -> str:
    return f"{value}/5"


def kpi_metric_for(concept: str, category: str) -> str:
    if _profile_for_concept(concept).category == "other":
        return "\u5bfe\u8c61\u7bc4\u56f2\u30fb\u5165\u529b\u6761\u4ef6\u3092\u6574\u7406"
    if concept == "AI-OCR業務自動化":
        return {"集客": "対象帳票数・入力経路", "行動": "読取精度・例外確認件数", "成果": "手入力削減時間・連携成功率"}[category]
    if concept == "定型業務自動化":
        return {"集客": "対象業務数・処理頻度", "行動": "処理成功率・例外発生率", "成果": "削減工数・入力ミス削減"}[category]
    if concept == "営業情報の一元管理":
        return {"集客": "顧客・商談登録率", "行動": "活動更新率・停滞検知数", "成果": "受注率・案件化率"}[category]
    if concept == "入力案件の業務改善":
        return {"集客": "対象範囲・利用者数", "行動": "運用定着率・処理品質", "成果": "削減時間・改善率"}[category]
    if concept == "採用強化":
        return {"集客": "採用ページ流入", "行動": "募集要項閲覧・社員紹介閲覧", "成果": "応募数・応募率"}[category]
    if concept == "物件検索強化":
        return {"集客": "物件検索流入", "行動": "物件詳細閲覧・お気に入り", "成果": "内見予約・問い合わせ数"}[category]
    if concept == "検索流入強化":
        return {"集客": "自然検索流入", "行動": "主要ページ回遊・FAQ閲覧", "成果": "問い合わせ件数・CV率"}[category]
    return {"集客": "アクセス数・流入経路", "行動": "サービス/実績閲覧・CTAクリック", "成果": "問い合わせ件数・CV率"}[category]


def extract_case_triplets(case_studies: str) -> list[dict[str, str]]:
    return build_case_triplets_from_items(extract_case_study_items(case_studies))


def build_case_triplets_from_items(items: list[str]) -> list[dict[str, str]]:
    triplets: list[dict[str, str]] = []
    for idx, item in enumerate(unique_items(items, 3), start=1):
        title = extract_case_title(item, idx)
        result = extract_labeled_segment(item, "成果") or extract_unlabeled_case_result(item)
        current = extract_current_segment(item)
        triplets.append(
            {
                "title": title,
                "current": current or case_current_hint(item, title, result),
                "action": extract_labeled_segment(item, "施策") or case_action_hint(f"{title} {item} {result}"),
                "result": result or case_result_hint(item),
            }
        )
    return triplets


def extract_case_title(item: str, index: int) -> str:
    title_match = re.match(r"^([^:：。]+)[:：]", item.strip())
    if title_match and not title_match.group(1) in {"現状", "施策", "成果"}:
        return title_match.group(1).strip()
    return f"Case {index}"


def remove_case_title(item: str) -> str:
    if re.match(r"^([^:：。]+)[:：]", item.strip()):
        return re.sub(r"^([^:：。]+)[:：]\s*", "", item.strip())
    return item


def extract_labeled_segment(item: str, label: str) -> str:
    match = re.search(rf"{label}\s*[:：]\s*(.*?)(?=(?:現状|施策|成果)\s*[:：]|。|;|；|\n|$)", item)
    return _trim(match.group(1), 42) if match else ""


def extract_current_segment(item: str) -> str:
    current = extract_labeled_segment(item, "現状")
    if current and not looks_like_case_result(current):
        return current
    return ""


def extract_unlabeled_case_result(item: str) -> str:
    body = remove_case_title(item)
    result_phrase = extract_case_result_phrase(body)
    if result_phrase:
        return _trim(result_phrase, 42)
    return ""


def looks_like_case_result(text: str) -> bool:
    return bool(re.search(r"(\d+[%％]|[0-9.]+倍|\d+件|増加|向上|CV率|問い合わせ件数|自然検索流入)", text))


def extract_case_result_phrase(text: str) -> str:
    patterns = [
        r"問い合わせ件数\s*\d+[%％]?\s*(?:増加|向上|改善)?",
        r"CV率\s*[0-9.]+\s*倍",
        r"CV率\s*\d+[%％]?\s*(?:増加|向上|改善)?",
        r"自然検索流入\s*\d+[%％]?\s*(?:増加|向上|改善)?",
        r"\d+[%％]\s*(?:増加|向上|改善)",
        r"[0-9.]+\s*倍",
        r"\d+件\s*(?:増加|獲得|改善)?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0).strip()
    return ""


def case_current_hint(item: str, title: str, result: str) -> str:
    combined = f"{title} {item} {result}"
    if _contains_any(combined, ["CV率", "転換率", "コンバージョン"]):
        return "サイト訪問後の問い合わせ転換率に課題があった案件"
    if _contains_any(combined, ["不動産", "物件", "賃貸", "売買"]):
        return "問い合わせ導線や物件情報の見せ方に改善余地があった案件"
    if _contains_any(combined, ["問い合わせ", "問合せ"]):
        return "問い合わせ導線やサービス訴求に改善余地があった案件"
    if _contains_any(combined, ["SEO", "検索", "自然検索", "流入"]):
        return "検索流入後の回遊と問い合わせ導線に改善余地があった案件"
    if _contains_any(combined, ["採用", "応募"]):
        return "採用情報の理解促進と応募導線に課題があった案件"
    return "Webサイト上の情報設計と成果導線に改善余地があった案件"


def case_action_hint(item: str) -> str:
    if _contains_any(item, ["CV率", "転換率", "コンバージョン"]):
        return "CTA配置改善、FAQ整備、導線短縮、問い合わせフォーム最適化"
    if _contains_any(item, ["不動産", "物件", "賃貸", "売買"]):
        return "CTA改善、フォーム導線改善、物件情報整理、CMS運用改善"
    if _contains_any(item, ["問い合わせ", "問合せ", "フォーム"]):
        return "CTA改善、フォーム導線改善、サービス訴求整理、CMS運用改善"
    if _contains_any(item, ["採用", "応募"]):
        return "採用コンテンツ整備、応募導線改善、FAQ整備、フォーム最適化"
    if _contains_any(item, ["SEO", "検索", "流入"]):
        return "SEO構造改善、コンテンツ整理、内部導線改善、CTA改善"
    if _contains_any(item, ["CMS", "更新"]):
        return "CMS設計、更新フロー整備、掲載情報整理、運用ルール策定"
    return "情報設計改善、CTA改善、FAQ整備、問い合わせフォーム最適化"


def case_result_hint(item: str) -> str:
    result_phrase = extract_case_result_phrase(item)
    if result_phrase:
        return _trim(result_phrase, 42)
    if _contains_any(item, ["問い合わせ", "CV"]):
        return "問い合わせ数とCV率を改善"
    if _contains_any(item, ["採用", "応募"]):
        return "応募導線の到達率を改善"
    return "成果につながった進め方を本提案へ反映"


def display_case_title(title: str, index: int) -> str:
    if re.match(r"^Case\s*\d+", title):
        return title
    return f"Case {index}：{title}"


def extract_client_name(client_company_info: str, fallback: str) -> str:
    for source in (client_company_info, fallback):
        for line in source.splitlines():
            candidate = re.sub(r"^(企業名|会社名|提案先企業名|提案先企業|提案先|顧客名|クライアント)\s*[:：]\s*", "", line.strip())
            candidate = candidate.strip(" ・-　")
            if candidate and not _looks_generic_client_name(candidate) and not candidate.lower().startswith(("http://", "https://")):
                return _trim(candidate, 36)
    return "提案先企業"


def extract_case_study_items(case_studies: str) -> list[str]:
    if not case_studies.strip():
        return []

    lines = [line.strip() for line in case_studies.splitlines() if line.strip()]
    if len(lines) <= 1:
        lines = [line.strip() for line in re.split(r"[。;；]+", case_studies) if line.strip()]

    cleaned = []
    for line in lines:
        item = re.sub(r"^[・•\-\d\s.．、]+", "", line.strip())
        item = re.sub(r"^(実績|事例|成功事例)\s*[:：]\s*", "", item)
        if item:
            cleaned.append(item)
    return unique_items(cleaned, 3)


def extract_project_points(project_brief: str) -> list[str]:
    text = project_brief.strip()
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.needs[:4]
    points = [
        "問い合わせ導線・CTAの改善" if _contains_any(text, ["問い合わせ", "問合せ", "CV", "コンバージョン"]) else "",
        "採用情報・応募導線の強化" if "採用" in text else "",
        "現行サイトの情報鮮度と構成整理" if _contains_any(text, ["情報が古", "古く", "リニューアル", "刷新"]) else "",
        "サービス内容が伝わる情報設計" if _contains_any(text, ["サービス内容", "伝わりにく", "訴求"]) else "",
        "予算・スコープの優先順位整理" if "予算" in text else "",
        "希望納期に合わせた進行設計" if _contains_any(text, ["納期", "早め", "急ぎ", "公開時期", "公開希望", "リリース希望"]) else "",
    ]
    return unique_items(points, 4)


def extract_solution_points(text: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.strategy_items[:4]
    points = [
        "問い合わせ導線を起点にCTAとページ遷移を再設計" if _contains_any(text, ["問い合わせ", "問合せ", "CV"]) else "",
        "採用候補者向けの情報整理と応募導線を強化" if "採用" in text else "",
        "情報設計とサービス訴求を再構成" if _contains_any(text, ["情報", "サービス内容", "訴求"]) else "",
        "CMS要件と更新運用フローを整理" if _contains_any(text, ["CMS", "更新"]) else "",
        "SEOを見据えたサイト構造とコンテンツを整理" if _contains_any(text, ["SEO", "検索"]) else "",
        "公開後の運用保守・改善サイクルを設計" if _contains_any(text, ["運用", "保守", "改善"]) else "",
    ]
    return unique_items(points, 4)


def extract_service_points(own_service_info: str) -> list[str]:
    extracted = extract_text_items(own_service_info, 3)
    profile = proposal_profile_for_text(own_service_info)
    if profile.category != "web":
        return unique_items(extracted + profile.services, 4)
    points = extracted + [
        "CMS構築・更新しやすい管理設計" if _contains_any(own_service_info, ["CMS", "更新"]) else "",
        "SEOを考慮した情報設計" if _contains_any(own_service_info, ["SEO", "検索"]) else "",
        "公開後の改善運用まで支援" if _contains_any(own_service_info, ["運用", "保守", "改善"]) else "",
    ]
    return unique_items(points, 4)


def extract_schedule_points(text: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.schedule[:4]
    points = [
        "初回ヒアリング・要件整理",
        "情報設計・ワイヤーフレーム",
        "デザイン・実装・CMS設定" if _contains_any(text, ["CMS", "更新"]) else "デザイン・実装",
        "公開・運用改善" if _contains_any(text, ["運用", "保守", "改善"]) else "公開前検証・リリース",
    ]
    if _contains_any(text, ["早め", "急ぎ", "短納期"]):
        points[0] = "早期提案に向けた要件整理"
    return unique_items(points, 4)


def extract_team_points(own_service_info: str) -> list[str]:
    profile = proposal_profile_for_text(own_service_info)
    if profile.category != "web":
        return profile.team[:4]
    points = [
        "進行管理・要件整理",
        "情報設計・UI/ビジュアル設計",
        "フロントエンド実装・CMS構築" if _contains_any(own_service_info, ["CMS", "実装", "構築"]) else "実装・検証",
        "公開後の更新・改善運用支援" if _contains_any(own_service_info, ["運用", "保守", "改善", "更新"]) else "公開後の軽微な更新相談",
    ]
    return unique_items(points, 4)


def extract_cost_points(text: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.cost_points[:4]
    has_budget_detail = "予算" in text and not _contains_any(text, ["予算は未定", "予算未定", "予算感未定"])
    points = [
        "予算に合わせて必須範囲を優先" if has_budget_detail else "予算確認後に必須範囲を確定",
        "ページ数・コンテンツ量で調整",
        "CMS・フォーム・SEOは要件に応じて別枠化" if _contains_any(text, ["CMS", "フォーム", "SEO", "検索"]) else "追加機能はオプション化",
        "運用保守・改善支援は月次範囲で検討" if _contains_any(text, ["運用", "保守", "改善"]) else "公開後支援は必要に応じて追加",
    ]
    return unique_items(points, 4)


def derive_estimate_summary(payload: PptxDownloadRequest, text: str) -> EstimateSummary:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        lines: list[dict[str, object]] = [
            {
                "name": line.name,
                "min": line.min,
                "max": line.max,
                "priority": line.priority,
                "enabled": not line.optional or _contains_any(text, ["運用", "保守", "改善", "支援", "継続", line.name]),
            }
            for line in profile.estimate_lines
        ]
        enabled_lines = [line for line in lines if bool(line["enabled"])]
        total_min = sum(int(line["min"]) for line in enabled_lines)
        total_max = sum(int(line["max"]) for line in enabled_lines)
        budget = extract_budget_amount(f"{payload.budget_range}\n{text}")
        if budget is None:
            budget_fit = "予算未入力"
            budget_label = "未入力"
        elif budget >= total_max:
            budget_fit = "予算内"
            budget_label = f"{budget}万円"
        elif budget >= total_min * 0.85:
            budget_fit = "やや調整必要"
            budget_label = f"{budget}万円"
        else:
            budget_fit = "予算超過の可能性あり"
            budget_label = f"{budget}万円"
        return EstimateSummary(
            page_count=max(1, len(profile.structure_items)),
            total_min=total_min,
            total_max=total_max,
            total_label=f"{total_min}万〜{total_max}万円",
            budget_label=budget_label,
            budget_fit=budget_fit,
            lines=lines,
            required=[str(line["name"]) for line in enabled_lines if line["priority"] == "必須対応"],
            recommended=[str(line["name"]) for line in enabled_lines if line["priority"] == "推奨対応"],
            optional=[str(line["name"]) for line in enabled_lines if line["priority"] == "オプション対応"],
        )

    page_count = extract_page_count(payload.estimated_page_count, text)
    page_base = max(8, page_count)
    has_cms = estimate_flag(payload.cms_required, text, ["CMS", "WordPress", "更新"])
    has_form = estimate_flag(payload.contact_form_required, text, ["問い合わせフォーム", "問合せフォーム", "フォーム", "資料請求"])
    has_special = estimate_flag(payload.special_function_required, text, ["物件検索", "検索機能", "会員", "予約", "決済", "特殊機能"])
    has_seo = estimate_flag(payload.seo_required, text, ["SEO", "自然検索", "検索流入"])
    has_content = estimate_flag(payload.content_creation_required, text, ["撮影", "原稿", "ライティング", "取材"])

    lines: list[dict[str, object]] = [
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
    enabled_lines = [line for line in lines if bool(line["enabled"])]
    total_min = sum(int(line["min"]) for line in enabled_lines)
    total_max = sum(int(line["max"]) for line in enabled_lines)
    budget = extract_budget_amount(f"{payload.budget_range}\n{text}")
    if budget is None:
        budget_fit = "予算未入力"
        budget_label = "未入力"
    elif budget >= total_max:
        budget_fit = "予算内"
        budget_label = f"{budget}万円"
    elif budget >= total_min * 0.85:
        budget_fit = "やや調整必要"
        budget_label = f"{budget}万円"
    else:
        budget_fit = "予算超過の可能性あり"
        budget_label = f"{budget}万円"

    return EstimateSummary(
        page_count=page_count,
        total_min=total_min,
        total_max=total_max,
        total_label=f"{total_min}万〜{total_max}万円",
        budget_label=budget_label,
        budget_fit=budget_fit,
        lines=lines,
        required=[str(line["name"]) for line in enabled_lines if line["priority"] == "必須対応"],
        recommended=[str(line["name"]) for line in enabled_lines if line["priority"] == "推奨対応"],
        optional=[str(line["name"]) for line in enabled_lines if line["priority"] == "オプション対応"],
    )


def extract_page_count(primary: str, text: str) -> int:
    for source in (primary, text):
        normalized = normalize_number_text(source)
        match = re.search(r"(\d+)\s*(?:ページ|頁|p)", normalized, flags=re.IGNORECASE)
        if match:
            return max(1, min(60, int(match.group(1))))
        number = re.search(r"\d+", normalized)
        if source == primary and number:
            return max(1, min(60, int(number.group(0))))
    return 10


def extract_budget_amount(text: str) -> int | None:
    normalized = normalize_number_text(text)
    amounts: list[int] = []
    for match in re.finditer(r"(\d+(?:\.\d+)?)\s*(万円|万|円)", normalized):
        amount = float(match.group(1))
        amounts.append(round(amount / 10000) if match.group(2) == "円" else round(amount))
    return max(amounts) if amounts else None


def normalize_number_text(text: str) -> str:
    return text.translate(str.maketrans("０１２３４５６７８９，", "0123456789,")).replace(",", "")


def estimate_flag(value: str, text: str, patterns: list[str]) -> bool:
    if _contains_any(value, ["なし", "不要", "無", "無し", "対象外"]):
        return False
    if _contains_any(value, ["あり", "有", "必要", "希望", "対象", "実施", "要"]):
        return True
    return _contains_any(text, patterns)


def extract_confirmation_items(text: str) -> list[str]:
    profile = proposal_profile_for_text(text)
    if profile.category != "web":
        return profile.confirmations[:5]
    has_budget_detail = "予算" in text and not _contains_any(text, ["予算は未定", "予算未定", "予算感未定"])
    items = [
        "予算感・上限・見積粒度" if not has_budget_detail else "予算内で優先する必須範囲",
        "希望公開時期・社内確認フロー" if not _contains_any(text, ["納期", "公開時期", "公開希望", "リリース希望", "早め", "急ぎ"]) else "希望納期に対する素材準備状況",
        "CMS要否・更新担当・更新頻度" if not _contains_any(text, ["CMS", "更新"]) else "CMS権限と更新担当範囲",
        "SEO対象キーワード・既存流入状況" if not _contains_any(text, ["SEO", "検索"]) else "SEO対象範囲と成果指標",
        "公開後の運用保守範囲" if not _contains_any(text, ["運用", "保守", "改善"]) else "運用改善の支援範囲と頻度",
    ]
    return unique_items(items, 5)


def extract_text_items(text: str, max_count: int) -> list[str]:
    if not text.strip():
        return []
    parts = []
    for line in re.split(r"[\n。;；]+", text):
        item = re.sub(r"^[・•\-\d\s.．、]+", "", line.strip())
        if item:
            parts.append(_trim(item, 48))
    return unique_items(parts, max_count)


def ensure_items(items: list[str], fallback: list[str], max_count: int) -> list[str]:
    merged = unique_items(items, max_count)
    fallback_index = 0
    while len(merged) < max_count and fallback and fallback_index < len(fallback) * 2:
        candidate = fallback[fallback_index % len(fallback)]
        if not _is_duplicate_text(candidate, merged):
            merged.append(candidate.strip())
        fallback_index += 1
    return merged[:max_count]


def unique_items(items: list[str], max_count: int | None = None) -> list[str]:
    unique: list[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned or _is_duplicate_text(cleaned, unique):
            continue
        unique.append(cleaned)
        if max_count and len(unique) >= max_count:
            break
    return unique


def build_solution_rows(items: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    used_hints: list[str] = []
    for idx, item in enumerate(unique_items(items, 4)):
        hint = _solution_hint(item, idx)
        if _is_duplicate_text(hint, used_hints):
            hint = _fallback_solution_hint(len(used_hints))
        used_hints.append(hint)
        rows.append([f"課題 {len(rows) + 1}", _trim(item, 32), _trim(hint, 46)])
    return rows


def _solution_hint(item: str, index: int = 0) -> str:
    if "AI-OCR" in item or "帳票" in item or "読取" in item or "読み取り" in item:
        return "対象帳票、抽出項目、連携先を整理し、PoCで精度を確認"
    if "API" in item or "CSV" in item or "連携" in item:
        return "既存システムとの連携条件を整理し、段階的に接続"
    if "RPA" in item or "定型" in item or "自動化" in item:
        return "手順と例外処理を標準化し、安定運用できる自動化へ"
    if "CRM" in item or "SFA" in item or "商談" in item:
        return "項目、権限、レポートを整理し、営業活動を可視化"
    if "導線" in item or "問い合わせ" in item:
        return "主要CTAとページ遷移を整理し、成果導線を明確化"
    if "情報" in item or "コンテンツ" in item:
        return "情報設計と訴求軸を再構成し、理解しやすい構成へ"
    if "運用" in item or "改善" in item:
        return "公開後の解析・改善サイクルを前提に設計"
    if "採用" in item:
        return "採用候補者向け情報と応募導線を整理"
    if "CMS" in item or "更新" in item:
        return "CMS要件と更新運用フローを設計"
    if "SEO" in item or "検索" in item:
        return "SEOを見据えたサイト構造とコンテンツを整理"
    return _fallback_solution_hint(index)


def _fallback_solution_hint(index: int) -> str:
    hints = [
        "要件整理を通じて優先度を明確化し、実行方針へ反映",
        "対象業務と利用者を整理し、導入しやすい構成へ再設計",
        "成果につながる接点を整理し、効果測定を明確化",
        "導入後の改善を見据えた運用しやすい設計に整備",
    ]
    return hints[index % len(hints)]


def _is_duplicate_text(value: str, existing_items: list[str]) -> bool:
    key = _normalize_text(value)
    return not key or any(key == _normalize_text(item) for item in existing_items)


def _normalize_text(value: str) -> str:
    cleaned = re.sub(r"[\s　・•\-ー、。,.．:：/／「」『』（）()\[\]]+", "", value.lower())
    cleaned = cleaned.replace("課題", "").replace("解決策", "")
    return cleaned


def _looks_generic_client_name(value: str) -> bool:
    normalized = _normalize_text(value)
    generic_words = {"提案先企業", "提案先企業情報", "企業情報", "会社情報", "提案先", "貴社", "お客様", "クライアント", "未入力"}
    return normalized in {_normalize_text(word) for word in generic_words}


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _fit_font_size(text: str, base_size: int) -> int:
    if len(text) > 34:
        return max(base_size - 6, 25)
    if len(text) > 24:
        return max(base_size - 3, 28)
    return base_size


def sanitize_proposal_text(text: str) -> str:
    replacements = {
        "変動する可能性があります": "変動します",
        "できる可能性があります": "できます",
        "進めやすい可能性があります": "進めやすい案件です",
        "可能性があります": "見込みです",
        "可能性がある": "余地があります",
        "確認が必要です": "次回確認事項として扱います",
        "整理する必要があります": "整理します",
        "精度を高める必要があります": "精度を高めます",
        "と考えられます": "と判断します",
        "実績イメージ": "関連実績",
    }
    cleaned = text
    for before, after in replacements.items():
        cleaned = cleaned.replace(before, after)
    return cleaned


def _trim(text: str, max_length: int) -> str:
    cleaned = sanitize_proposal_text(text.strip().replace("\n", " "))
    if len(cleaned) <= max_length:
        return cleaned
    return f"{cleaned[: max_length - 1]}…"


def rank_probability_for(rank: str) -> int:
    if rank == "A":
        return 80
    if rank == "D":
        return 20
    if rank == "C":
        return 40
    return 60


def risk_score_for_probability(probability: int, risk_count: int) -> int:
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


def risk_label_for(score: int) -> str:
    normalized = max(1, min(5, score))
    return f"{'★' * normalized}{'☆' * (5 - normalized)}"


def projected_probability_for(probability: int, risk_score: int, action_count: int) -> int:
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


def strip_probability_label(label: str) -> str:
    cleaned = re.sub(r"受注確率\s*\d+[%％]\s*[|｜]\s*", "", label)
    return cleaned or label


def rank_color_for(rank: str) -> str:
    if rank == "A":
        return COLORS["green"]
    if rank in {"C", "D"}:
        return COLORS["red"]
    return COLORS["blue"]


def rank_light_color_for(rank: str) -> str:
    if rank == "A":
        return COLORS["green_light"]
    if rank in {"C", "D"}:
        return COLORS["red_light"]
    return COLORS["blue_light"]
