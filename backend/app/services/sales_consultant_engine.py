from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Literal

from app.models import ProposalAnalysis, ProposalRequest


EvidenceKind = Literal["input_fact", "derived_fact", "hypothesis", "requires_confirmation"]


@dataclass(frozen=True)
class EvidenceStatement:
    label: str
    value: str
    kind: EvidenceKind
    basis: str


@dataclass(frozen=True)
class CustomerAnalysis:
    company_size: EvidenceStatement
    industry: EvidenceStatement
    maturity: EvidenceStatement
    dx_level: EvidenceStatement
    ai_usage: EvidenceStatement
    decision_speed: EvidenceStatement
    organization: EvidenceStatement
    culture: EvidenceStatement
    budget_sense: EvidenceStatement


@dataclass(frozen=True)
class IndustryAnalysis:
    market_issues: list[str]
    competition_factors: list[str]
    regulations: list[str]
    talent_issues: list[str]
    dx_status: str
    ai_status: str
    common_kpis: list[str]
    decision_points: list[str]


@dataclass(frozen=True)
class DecisionMakerAnalysis:
    primary_decision_maker: str
    likely_influencers: list[str]
    priorities: list[str]
    expected_concerns: list[str]
    opposition_risks: list[str]
    recommended_order: list[str]


@dataclass(frozen=True)
class CompetitiveStrategy:
    situation: str
    winning_strategy: str
    differentiation: list[str]
    advantages: list[str]
    loss_factors: list[str]
    risks: list[str]


@dataclass(frozen=True)
class ObjectionPlan:
    objection: str
    answer: str
    recommended_slide: str
    evidence_needed: str


@dataclass(frozen=True)
class SalesConsultantBrief:
    customer: CustomerAnalysis
    industry: IndustryAnalysis
    decision_maker: DecisionMakerAnalysis
    business_issues: list[EvidenceStatement]
    proposal_strategy: str
    proposal_position: str
    win_strategy: str
    value_proposition: str
    story_arc: list[str]
    executive_summary: list[str]
    objections: list[ObjectionPlan]
    roi_plan: list[str]
    roadmap: list[str]
    reviewer_notes: list[str]
    missing_information: list[str]
    confidence: float


def build_sales_consultant_brief(payload: ProposalRequest) -> SalesConsultantBrief:
    text = _collect_text(payload)
    industry = _infer_industry(text)
    project_type = _infer_project_type(text)
    customer = _build_customer_analysis(payload, text, industry)
    industry_analysis = _build_industry_analysis(industry, project_type)
    decision_maker = _build_decision_maker_analysis(text, industry, project_type)
    issues = _build_business_issues(text, industry, project_type)
    proposal_strategy = _choose_proposal_strategy(text, issues, project_type)
    proposal_position = _proposal_position_for(proposal_strategy, project_type)
    competitive = _build_competitive_strategy(payload, text, industry, project_type, proposal_strategy)
    value = _build_value_proposition(customer, proposal_strategy, competitive, issues)
    story = _build_story_arc(proposal_strategy, decision_maker)
    executive_summary = _build_executive_summary(customer, issues, value, proposal_strategy, competitive)
    objections = _build_objections(text, project_type, proposal_strategy)
    roi_plan = _build_roi_plan(project_type, industry)
    roadmap = _build_roadmap(project_type)
    missing = _missing_information(payload, text)
    reviewer_notes = _build_reviewer_notes(issues, competitive, objections, missing)
    confidence = _confidence(payload, missing)

    return SalesConsultantBrief(
        customer=customer,
        industry=industry_analysis,
        decision_maker=decision_maker,
        business_issues=issues,
        proposal_strategy=proposal_strategy,
        proposal_position=proposal_position,
        win_strategy=competitive.winning_strategy,
        value_proposition=value,
        story_arc=story,
        executive_summary=executive_summary,
        objections=objections,
        roi_plan=roi_plan,
        roadmap=roadmap,
        reviewer_notes=reviewer_notes,
        missing_information=missing,
        confidence=confidence,
    )


def build_sales_consultant_prompt_section(brief: SalesConsultantBrief) -> str:
    """Internal-only prompt context. The model must use it but not expose engine names."""
    data = asdict(brief)
    objections = "\n".join(
        f"- {item['objection']} / 回答案: {item['answer']} / 必要根拠: {item['evidence_needed']}"
        for item in data["objections"]
    )
    issues = "\n".join(
        f"- {item['value']} ({item['kind']}: {item['basis']})" for item in data["business_issues"]
    )
    return f"""
## Internal Sales Consultant Strategy Context
Do not show internal engine names in the customer-facing proposal.
Use this context to decide what to say, in what order, and what must remain a hypothesis.

- Customer industry: {data['customer']['industry']['value']} ({data['customer']['industry']['kind']})
- Company size: {data['customer']['company_size']['value']} ({data['customer']['company_size']['kind']})
- Maturity: {data['customer']['maturity']['value']}
- DX level: {data['customer']['dx_level']['value']}
- AI usage: {data['customer']['ai_usage']['value']}
- Decision maker: {data['decision_maker']['primary_decision_maker']}
- Proposal strategy: {data['proposal_strategy']}
- Proposal position: {data['proposal_position']}
- Winning strategy: {data['win_strategy']}
- Value proposition: {data['value_proposition']}
- Story arc: {' -> '.join(data['story_arc'])}
- Executive summary focus: {' / '.join(data['executive_summary'])}
- ROI plan: {' / '.join(data['roi_plan'])}
- Roadmap: {' / '.join(data['roadmap'])}
- Missing information: {' / '.join(data['missing_information'])}

Business issues:
{issues}

Likely objections:
{objections}

Senior consultant review notes:
{chr(10).join(f"- {note}" for note in data['reviewer_notes'])}
""".strip()


def enrich_analysis_with_sales_consultant_strategy(
    analysis: ProposalAnalysis,
    brief: SalesConsultantBrief,
) -> ProposalAnalysis:
    data = analysis.dict()
    data["project_summary"] = _prepend_unique_sentence(data["project_summary"], _summary_sentence(brief))
    data["proposal_policy"] = _prepend_unique_sentence(data["proposal_policy"], _policy_sentence(brief))
    data["proposal_story"] = _story_sentence(brief)
    data["proposal_structure"] = _merge_structure(data.get("proposal_structure", []), brief)
    data["expected_questions_and_answers"] = _merge_expected_questions(data.get("expected_questions_and_answers", []), brief)
    data["quality_check"] = _merge_quality_check(data.get("quality_check", {}), brief)
    data["powerpoint_generation_data"] = _enrich_powerpoint_data(data.get("powerpoint_generation_data", {}), brief)
    data["slide_scripts"] = _sync_slide_scripts(data["powerpoint_generation_data"])
    return ProposalAnalysis.parse_obj(data)


def _collect_text(payload: ProposalRequest) -> str:
    return "\n".join(
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


def _build_customer_analysis(payload: ProposalRequest, text: str, industry: str) -> CustomerAnalysis:
    return CustomerAnalysis(
        company_size=_statement("企業規模", _infer_company_size(text), _has_any(text, ["大企業", "中小", "社員", "名", "店舗", "拠点"])),
        industry=_statement("業界", industry, industry != "業界未特定"),
        maturity=_statement("成熟度", _infer_maturity(text), _has_any(text, ["既存", "運用", "導入済", "Excel", "紙", "手作業"])),
        dx_level=_statement("DXレベル", _infer_dx_level(text), _has_any(text, ["DX", "システム", "API", "CSV", "Excel", "紙"])),
        ai_usage=_statement("AI活用度", _infer_ai_usage(text), _has_any(text, ["AI", "OCR", "生成AI", "チャットボット", "画像認識"])),
        decision_speed=_statement("意思決定速度", _infer_decision_speed(payload.desired_launch_timing, text), bool(payload.desired_launch_timing)),
        organization=_statement("組織構造", _infer_organization(text, industry), _has_any(text, ["部門", "現場", "情報システム", "経営", "担当"])),
        culture=_statement("文化", _infer_culture(text), _has_any(text, ["品質", "スピード", "慎重", "現場", "承認"])),
        budget_sense=_statement("予算感", payload.budget_range.strip() or "予算は次回確認", bool(payload.budget_range.strip())),
    )


def _build_industry_analysis(industry: str, project_type: str) -> IndustryAnalysis:
    base = {
        "製造業": (
            ["品質ばらつき", "紙・Excel運用", "現場負荷", "技能継承"],
            ["品質", "納期", "原価", "現場定着"],
            ["安全衛生", "品質管理", "取引先監査"],
            ["熟練者不足", "現場教育", "多能工化"],
            ["工場単位で段階的に進む傾向"],
            ["検査・予兆保全・画像認識から導入されやすい"],
            ["不良率", "確認時間", "手戻り件数", "稼働率"],
            ["現場負荷", "投資対効果", "既存設備連携"],
        ),
        "医療": (
            ["人手不足", "安全性", "記録負荷", "患者対応品質"],
            ["安全性", "業務負荷", "説明責任"],
            ["個人情報", "医療安全", "監査対応"],
            ["専門職不足", "教育時間", "夜間対応"],
            ["部門別に慎重な検証が必要"],
            ["診療支援よりも事務・記録支援から入りやすい"],
            ["対応時間", "記録時間", "ミス件数", "満足度"],
            ["安全性", "個人情報", "現場負荷"],
        ),
        "教育・自治体": (
            ["問い合わせ分散", "職員負荷", "説明品質", "予算制約"],
            ["公平性", "説明責任", "運用しやすさ"],
            ["個人情報", "アクセシビリティ", "調達手続き"],
            ["職員負荷", "属人化", "年度切替"],
            ["PoCと合意形成を重視"],
            ["FAQ、検索、問い合わせ分類から導入されやすい"],
            ["回答時間", "一次解決率", "問い合わせ件数", "職員工数"],
            ["予算根拠", "住民・保護者への説明", "運用体制"],
        ),
    }
    defaults = (
        ["業務効率", "品質均一化", "ナレッジ不足", "顧客対応"],
        ["価格", "品質", "スピード", "導入後の支援"],
        ["契約条件", "個人情報", "セキュリティ"],
        ["担当者不足", "教育負荷", "属人化"],
        ["既存業務を残しながら段階導入する傾向"],
        "AIはPoCで効果検証してから本導入判断されやすい",
        ["作業時間", "ミス件数", "処理件数", "満足度"],
        ["費用対効果", "導入負荷", "既存業務との整合性"],
    )
    market, competition, regulations, talent, dx_status, ai_status, kpis, decision = base.get(industry, defaults)
    if project_type == "Web改善":
        market = ["問い合わせ導線", "情報更新", "検索流入", "ブランド信頼"] + market[:2]
        kpis = ["問い合わせ数", "CVR", "更新時間", "直帰率"]
    return IndustryAnalysis(
        market_issues=list(market),
        competition_factors=list(competition),
        regulations=list(regulations),
        talent_issues=list(talent),
        dx_status=dx_status[0] if isinstance(dx_status, list) else dx_status,
        ai_status=ai_status[0] if isinstance(ai_status, list) else ai_status,
        common_kpis=list(kpis),
        decision_points=list(decision),
    )


def _build_decision_maker_analysis(text: str, industry: str, project_type: str) -> DecisionMakerAnalysis:
    decision_maker = _infer_decision_maker(text, industry, project_type)
    priorities = {
        "経営者": ["投資対効果", "競争優位", "導入リスク", "意思決定の速さ"],
        "部長": ["部門成果", "予算整合", "導入体制", "他部門調整"],
        "現場責任者": ["現場負荷", "使いやすさ", "教育工数", "例外対応"],
        "情報システム": ["セキュリティ", "既存連携", "運用保守", "権限管理"],
    }
    selected = priorities.get(decision_maker, ["費用対効果", "導入負荷", "品質", "スケジュール"])
    return DecisionMakerAnalysis(
        primary_decision_maker=decision_maker,
        likely_influencers=_unique(["現場責任者", "情報システム", "経営層", "業務担当"], 4),
        priorities=selected,
        expected_concerns=["費用の妥当性", "現場に定着するか", "既存業務への影響", "効果測定の方法"],
        opposition_risks=["導入負荷が大きい", "ROIが見えにくい", "運用担当が決まらない"],
        recommended_order=["背景と課題", "事業インパクト", "導入方法", "費用対効果", "リスク対応", "次の判断事項"],
    )


def _build_business_issues(text: str, industry: str, project_type: str) -> list[EvidenceStatement]:
    candidates: list[tuple[str, bool, str]] = [
        ("手作業・確認作業に時間がかかっている", _has_any(text, ["手作業", "目視", "確認", "時間", "工数"]), "入力文に作業負荷の記述あり"),
        ("品質や判断基準が属人化している", _has_any(text, ["属人", "ばらつき", "品質", "ミス", "誤"]), "入力文に品質・ミスの記述あり"),
        ("既存システムやデータ連携が提案成功の鍵になる", _has_any(text, ["API", "CSV", "連携", "既存システム"]), "連携条件の記述あり"),
        ("投資対効果を説明しないと意思決定が進みにくい", _has_any(text, ["予算", "ROI", "費用", "投資"]), "予算または費用の記述あり"),
    ]
    if project_type == "Web改善":
        candidates.append(("問い合わせ導線と情報更新が営業成果に影響している", True, "Web改善案件の一般的な論点"))
    elif "AI" in project_type:
        candidates.append(("AIは完全自動化ではなく、人の確認を残す設計が現実的", True, "AI導入案件の一般的な論点"))
    issues = [_statement("課題", value, known, basis) for value, known, basis in candidates]
    return issues[:5]


def _build_competitive_strategy(
    payload: ProposalRequest,
    text: str,
    industry: str,
    project_type: str,
    proposal_strategy: str,
) -> CompetitiveStrategy:
    competitor_known = bool(payload.competitor_company_name.strip() or payload.competitor_site_url.strip())
    if competitor_known:
        situation = "競合あり"
    elif _has_any(text, ["価格", "相見積", "比較", "競合"]):
        situation = "価格・比較競争の可能性"
    else:
        situation = "競合未確認"
    winning = f"{proposal_strategy}を軸に、提案範囲・導入後運用・効果測定まで一体で示す"
    return CompetitiveStrategy(
        situation=situation,
        winning_strategy=winning,
        differentiation=[
            "提案書だけでなく導入後の運用定着まで説明する",
            "仮説と確認事項を分け、顧客が判断しやすい状態にする",
            "KPIと次回合意事項を明確にし、意思決定を前に進める",
        ],
        advantages=[
            f"{industry}の論点に合わせた提案ストーリー",
            f"{project_type}の導入手順とリスク対応をセットで提示",
        ],
        loss_factors=[
            "価格だけで比較される",
            "決裁者ごとの関心に答えきれない",
            "効果測定が曖昧なまま進む",
        ],
        risks=[
            "競合情報が不足している場合は仮説として提示する",
            "実績・ROIは入力根拠がない限り断定しない",
        ],
    )


def _build_value_proposition(
    customer: CustomerAnalysis,
    proposal_strategy: str,
    competitive: CompetitiveStrategy,
    issues: list[EvidenceStatement],
) -> str:
    primary_issue = issues[0].value if issues else "重要課題"
    return (
        f"{customer.industry.value}の{primary_issue}に対し、{proposal_strategy}を中心に、"
        f"現場が使える導入手順と効果測定まで示すことで、顧客が社内説明しやすい提案にする。"
    )


def _build_story_arc(proposal_strategy: str, decision_maker: DecisionMakerAnalysis) -> list[str]:
    if decision_maker.primary_decision_maker == "経営者":
        return ["現状", "経営課題", "投資判断の論点", proposal_strategy, "導入ロードマップ", "ROI/KPI", "意思決定事項"]
    if decision_maker.primary_decision_maker == "現場責任者":
        return ["現状業務", "現場課題", "原因", "改善後の流れ", "導入手順", "運用負荷", "次の確認事項"]
    return ["現状", "課題", "原因", "解決策", "導入方法", "効果", "今後"]


def _build_executive_summary(
    customer: CustomerAnalysis,
    issues: list[EvidenceStatement],
    value: str,
    proposal_strategy: str,
    competitive: CompetitiveStrategy,
) -> list[str]:
    primary_issue = issues[0].value if issues else "重要課題"
    return [
        f"背景: {customer.industry.value}では{primary_issue}が提案上の重要論点",
        f"結論: {proposal_strategy}で顧客の意思決定を前に進める",
        f"価値: {value}",
        f"勝ち筋: {competitive.winning_strategy}",
        "判断事項: 対象範囲、予算、スケジュール、次回確認事項を合意する",
    ]


def _build_objections(text: str, project_type: str, proposal_strategy: str) -> list[ObjectionPlan]:
    objections = [
        ObjectionPlan("費用が高い", "必須・推奨・オプションに分け、まず判断できる範囲を明確にします。", "見積・ROI", "予算上限と必須範囲"),
        ObjectionPlan("効果が見えにくい", "SMART KPIで現状値、目標、測定方法、測定タイミングを定義します。", "KPI・効果", "現状値または測定可能な代替指標"),
        ObjectionPlan("現場負荷が大きい", "PoCまたは段階導入で、現場確認を残しながら運用定着を検証します。", "導入ロードマップ", "担当者、対象部署、例外対応"),
        ObjectionPlan("競合との違いが分からない", f"{proposal_strategy}と導入後運用まで含めた勝ち筋で比較します。", "勝ち筋と差別化", "競合名、比較軸、選定基準"),
    ]
    if "AI" in project_type:
        objections.append(
            ObjectionPlan("AI精度が不安", "完全自動化ではなく候補提示と人の最終確認を前提に、精度と修正率を検証します。", "PoC計画", "評価データ、目標精度、修正率")
        )
    return objections[:5]


def _build_roi_plan(project_type: str, industry: str) -> list[str]:
    if project_type == "Web改善":
        return ["問い合わせ数", "CVR", "更新作業時間", "商談化率"]
    if "AI" in project_type:
        return ["確認時間", "人手修正率", "処理件数", "誤判定率"]
    if project_type == "RPA/業務自動化":
        return ["作業時間", "例外件数", "自動化率", "差し戻し件数"]
    return ["作業時間", "ミス件数", "処理件数", "満足度"]


def _build_roadmap(project_type: str) -> list[str]:
    if "AI" in project_type:
        return ["要件・評価基準", "データ確認", "PoC", "現場検証", "本導入判断"]
    return ["要件整理", "設計", "制作・実装", "確認・修正", "公開・運用開始"]


def _build_reviewer_notes(
    issues: list[EvidenceStatement],
    competitive: CompetitiveStrategy,
    objections: list[ObjectionPlan],
    missing: list[str],
) -> list[str]:
    notes = [
        "最初の2ページで、背景・課題・結論・期待効果・判断事項が分かる構成にする",
        f"勝ち筋は「{competitive.winning_strategy}」に寄せ、単なる機能説明で終わらせない",
        "断定できない競合・ROI・実績は仮説または確認事項として明示する",
        "顧客が社内説明しやすいよう、次回合意事項を最後に明確化する",
    ]
    if missing:
        notes.append(f"営業担当者は提出前に {', '.join(missing[:3])} を確認する")
    if objections:
        notes.append(f"最も想定される反対意見「{objections[0].objection}」への回答を資料内に入れる")
    return notes


def _missing_information(payload: ProposalRequest, text: str) -> list[str]:
    missing = []
    if not payload.budget_range.strip():
        missing.append("予算上限")
    if not payload.desired_launch_timing.strip():
        missing.append("希望時期")
    if not payload.competitor_company_name.strip() and not payload.competitor_site_url.strip():
        missing.append("競合情報")
    if not _has_any(text, ["決裁", "経営", "部長", "責任者", "情報システム"]):
        missing.append("意思決定者")
    if not payload.case_studies.strip():
        missing.append("根拠に使える実績")
    return missing


def _confidence(payload: ProposalRequest, missing: list[str]) -> float:
    base = 0.88
    base -= min(0.35, len(missing) * 0.06)
    if payload.hearing_result.strip():
        base += 0.04
    if payload.case_studies.strip():
        base += 0.03
    return round(max(0.45, min(0.95, base)), 2)


def _infer_industry(text: str) -> str:
    patterns = [
        ("製造業", ["製造", "工場", "検査", "品質", "生産"]),
        ("医療", ["医療", "病院", "クリニック", "患者", "診療"]),
        ("教育・自治体", ["教育", "学校", "自治体", "市役所", "保護者", "職員"]),
        ("不動産", ["不動産", "物件", "賃貸", "売買"]),
        ("物流", ["物流", "配送", "配車", "倉庫"]),
        ("小売・EC", ["小売", "EC", "店舗", "通販"]),
        ("人材・採用", ["採用", "求人", "人材", "応募"]),
        ("建設", ["建設", "施工", "現場", "工事"]),
        ("IT・SaaS", ["SaaS", "IT", "システム", "アプリ"]),
    ]
    for label, keywords in patterns:
        if _has_any(text, keywords):
            return label
    return "業界未特定"


def _infer_project_type(text: str) -> str:
    if _has_any(text, ["AI-OCR", "OCR", "帳票"]):
        return "AI-OCR"
    if _has_any(text, ["画像認識", "画像", "分類"]):
        return "AI画像認識"
    if _has_any(text, ["生成AI", "ナレッジ", "検索", "チャットボット"]):
        return "生成AI/ナレッジAI"
    if _has_any(text, ["RPA", "自動化"]):
        return "RPA/業務自動化"
    if _has_any(text, ["CRM", "SFA", "営業管理"]):
        return "CRM/SFA"
    if _has_any(text, ["Web", "サイト", "SEO", "CMS", "問い合わせ"]):
        return "Web改善"
    if _has_any(text, ["DX", "デジタル"]):
        return "DX推進"
    return "業務改善"


def _infer_company_size(text: str) -> str:
    if _has_any(text, ["大企業", "上場", "1000名", "千名", "全国"]):
        return "大企業"
    if _has_any(text, ["中堅", "300名", "500名", "複数拠点"]):
        return "中堅企業"
    if _has_any(text, ["中小", "少人数", "50名", "100名"]):
        return "中小企業"
    return "企業規模は仮説"


def _infer_maturity(text: str) -> str:
    if _has_any(text, ["紙", "Excel", "手作業", "属人"]):
        return "業務標準化前の改善余地が大きい"
    if _has_any(text, ["API", "CRM", "既存システム", "データ連携"]):
        return "既存システムを活かした段階改善が可能"
    return "成熟度は初回ヒアリングで確認"


def _infer_dx_level(text: str) -> str:
    if _has_any(text, ["API", "データ", "CRM", "SFA", "既存システム"]):
        return "中程度以上"
    if _has_any(text, ["紙", "Excel", "メール", "手作業"]):
        return "初期段階"
    return "DXレベルは仮説"


def _infer_ai_usage(text: str) -> str:
    if _has_any(text, ["AI", "OCR", "生成AI", "画像認識", "チャットボット"]):
        return "AI導入検討中"
    return "AI活用度は未確認"


def _infer_decision_speed(timing: str, text: str) -> str:
    if _has_any(timing + text, ["急ぎ", "至急", "来月", "3か月", "年度内"]):
        return "早い"
    if timing:
        return "通常"
    return "未確認"


def _infer_organization(text: str, industry: str) -> str:
    if _has_any(text, ["情報システム", "情シス"]):
        return "情報システムが関与する組織"
    if _has_any(text, ["現場", "担当者", "責任者"]):
        return "現場責任者と業務担当が関与"
    if industry == "教育・自治体":
        return "複数関係者で合意形成する組織"
    return "組織構造は仮説"


def _infer_culture(text: str) -> str:
    if _has_any(text, ["品質", "監査", "正確"]):
        return "品質・正確性重視"
    if _has_any(text, ["スピード", "短縮", "効率"]):
        return "スピード・効率重視"
    if _has_any(text, ["承認", "稟議", "決裁"]):
        return "合意形成重視"
    return "文化は仮説"


def _infer_decision_maker(text: str, industry: str, project_type: str) -> str:
    if _has_any(text, ["社長", "経営", "役員", "CEO"]):
        return "経営者"
    if _has_any(text, ["部長", "本部長"]):
        return "部長"
    if _has_any(text, ["現場責任者", "工場長", "店長"]):
        return "現場責任者"
    if _has_any(text, ["情報システム", "情シス", "IT担当"]):
        return "情報システム"
    if industry in {"製造業", "物流"}:
        return "現場責任者"
    if "AI" in project_type:
        return "部長"
    return "部長"


def _choose_proposal_strategy(text: str, issues: list[EvidenceStatement], project_type: str) -> str:
    if _has_any(text, ["売上", "問い合わせ", "CV", "応募", "集客"]):
        return "売上・成果向上重視"
    if _has_any(text, ["ミス", "品質", "ばらつき", "精度"]):
        return "品質改善重視"
    if _has_any(text, ["リスク", "監査", "セキュリティ"]):
        return "リスク低減重視"
    if "AI" in project_type:
        return "AI活用による業務高度化"
    if _has_any(text, ["時間", "工数", "効率", "自動化"]):
        return "業務効率・コスト削減重視"
    return "DX推進・業務改善重視"


def _proposal_position_for(strategy: str, project_type: str) -> str:
    if "売上" in strategy:
        return "売上向上"
    if "品質" in strategy:
        return "品質改善"
    if "リスク" in strategy:
        return "リスク低減"
    if "AI" in strategy:
        return "AI導入"
    if project_type == "Web改善":
        return "Web改善"
    return "業務改善"


def _statement(label: str, value: str, known: bool, basis: str = "") -> EvidenceStatement:
    return EvidenceStatement(
        label=label,
        value=value,
        kind="input_fact" if known else "hypothesis",
        basis=basis or ("入力情報から判断" if known else "入力情報が不足しているため仮説"),
    )


def _summary_sentence(brief: SalesConsultantBrief) -> str:
    return f"{brief.customer.industry.value}の状況を踏まえ、{brief.proposal_strategy}を軸にした提案として整理します。"


def _policy_sentence(brief: SalesConsultantBrief) -> str:
    return f"提案戦略は「{brief.proposal_strategy}」。勝ち筋は「{brief.win_strategy}」。価値提案は「{brief.value_proposition}」です。"


def _story_sentence(brief: SalesConsultantBrief) -> str:
    return " → ".join(brief.story_arc)


def _merge_structure(existing: list[dict[str, Any]], brief: SalesConsultantBrief) -> list[dict[str, str]]:
    additions = [
        ("顧客理解と背景", "顧客の業界・成熟度・意思決定者を整理する", brief.executive_summary[0]),
        ("提案戦略", "提案前に勝ち筋とポジションを明確にする", brief.win_strategy),
        ("反対意見への回答", "顧客が懸念しそうな点を先回りして説明する", brief.objections[0].answer),
        ("ROI/KPI", "導入判断に必要な効果測定の軸を示す", "、".join(brief.roi_plan[:4])),
    ]
    merged = list(existing)
    existing_sections = {_normalize(str(item.get("section", ""))) for item in merged}
    for section, objective, key_message in additions:
        if _normalize(section) not in existing_sections:
            merged.append({"section": section, "objective": objective, "key_message": key_message})
    return merged[:16]


def _merge_expected_questions(existing: list[dict[str, str]], brief: SalesConsultantBrief) -> list[dict[str, str]]:
    merged = list(existing)
    for objection in brief.objections:
        merged.append({"question": objection.objection, "answer": objection.answer})
    return _dedupe_dicts(merged, "question", 12)


def _merge_quality_check(existing: dict[str, str], brief: SalesConsultantBrief) -> dict[str, str]:
    updated = dict(existing)
    updated["competitive_differentiation"] = _append_text(
        updated.get("competitive_differentiation", ""),
        f"勝ち筋: {brief.win_strategy}。差別化: {brief.value_proposition}",
    )
    updated["alignment_with_customer_issues"] = _append_text(
        updated.get("alignment_with_customer_issues", ""),
        f"主要課題: {brief.business_issues[0].value if brief.business_issues else '顧客課題'}",
    )
    updated["human_review_notes"] = _append_text(
        updated.get("human_review_notes", ""),
        f"提出前確認: {', '.join(brief.missing_information[:4]) if brief.missing_information else '重大な不足情報なし'}",
    )
    updated["proposal_coverage"] = _append_text(
        updated.get("proposal_coverage", ""),
        "顧客分析、業界分析、意思決定者、勝ち筋、ROI、反対意見、ロードマップを反映済み。",
    )
    updated.setdefault("logical_consistency", "営業戦略からストーリー、KPI、次のアクションまで一貫しています。")
    updated.setdefault("typos", "提出前に固有名詞と数値を確認してください。")
    return updated


def _enrich_powerpoint_data(powerpoint: dict[str, Any], brief: SalesConsultantBrief) -> dict[str, Any]:
    updated = dict(powerpoint)
    slides = list(updated.get("slides") or [])
    strategic_slides = [
        _slide("経営層向け提案サマリー", brief.executive_summary[:4], "3つの結論カード", "最初に結論と判断事項を伝えます。"),
        _slide("勝ち筋と差別化", [brief.win_strategy, *brief.industry.competition_factors[:2], brief.value_proposition], "差別化カード", "競合比較ではなく、勝ち筋を説明します。"),
        _slide("想定される懸念と回答", [f"{item.objection}: {item.answer}" for item in brief.objections[:4]], "懸念と回答の2列カード", "顧客が反対しそうな点を先回りして説明します。"),
        _slide("ROI/KPI設計", [f"{item}: 現状値・目標値・測定方法を次回確認" for item in brief.roi_plan[:4]], "KPIカード", "根拠のない数値は作らず、測定設計を示します。"),
        _slide("導入ロードマップ", brief.roadmap, "ガントチャート風ロードマップ", "段階導入と意思決定地点を説明します。"),
    ]
    slides = _insert_missing_slides(slides, strategic_slides)
    updated["slides"] = _renumber_slide_dicts(slides[:18])
    return updated


def _slide(title: str, bullets: list[str], visual: str, notes: str) -> dict[str, Any]:
    return {
        "slide_no": 0,
        "layout": "content",
        "title": title,
        "bullets": [bullet for bullet in bullets if bullet][:4],
        "speaker_notes": notes,
        "visual_suggestion": visual,
    }


def _insert_missing_slides(existing: list[dict[str, Any]], additions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    titles = {_normalize(str(slide.get("title", ""))) for slide in existing}
    result = list(existing)
    insert_index = 1 if result else 0
    for slide in additions:
        if _normalize(slide["title"]) in titles:
            continue
        result.insert(insert_index, slide)
        insert_index += 1
    return result


def _sync_slide_scripts(powerpoint: dict[str, Any]) -> list[dict[str, Any]]:
    scripts = []
    for slide in powerpoint.get("slides", []):
        scripts.append(
            {
                "slide_no": slide.get("slide_no", 0),
                "section": slide.get("title", ""),
                "title": slide.get("title", ""),
                "body": slide.get("bullets", []),
                "speaker_notes": slide.get("speaker_notes", ""),
                "visual_suggestion": slide.get("visual_suggestion", ""),
            }
        )
    return scripts


def _renumber_slide_dicts(slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**slide, "slide_no": index} for index, slide in enumerate(slides, start=1)]


def _prepend_unique_sentence(existing: str, sentence: str) -> str:
    if sentence in existing:
        return existing
    return f"{sentence}\n{existing}".strip()


def _append_text(existing: str, addition: str) -> str:
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing}\n{addition}"


def _dedupe_dicts(items: list[dict[str, str]], key: str, limit: int) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for item in items:
        value = _normalize(str(item.get(key, "")))
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(item)
        if len(result) >= limit:
            break
    return result


def _unique(items: list[str], limit: int) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = re.sub(r"\s+", " ", item).strip()
        key = _normalize(cleaned)
        if not cleaned or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _has_any(text: str, keywords: list[str]) -> bool:
    normalized = text.lower()
    return any(keyword.lower() in normalized for keyword in keywords)


def _normalize(value: str) -> str:
    return re.sub(r"[\s　・、。,.()\[\]「」『』:：/\\-]+", "", value.lower())
