from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.models import PowerPointData, PowerPointSlide
from app.services.customer_ready_judgement import assessment_to_acceptance_scores, assess_customer_ready_deck


CONSULTING_BENCHMARKS = ["BCG", "Accenture", "Deloitte", "PwC", "NRI", "IBM Consulting"]


@dataclass(frozen=True)
class PersonaReview:
    persona: str
    score: int
    verdict: str
    thoughts: list[str]
    strengths: list[str]
    concerns: list[str]
    required_fixes: list[str]


@dataclass(frozen=True)
class BenchmarkReview:
    benchmark: str
    score: int
    structure: int
    story: int
    readability: int
    persuasion: int
    notes: list[str]


@dataclass(frozen=True)
class RedTeamFinding:
    severity: str
    issue: str
    impact: str
    improvement: str


@dataclass(frozen=True)
class SlideReview:
    slide_no: int
    title: str
    has_conclusion: bool
    text_volume: str
    readability_score: int
    design_score: int
    persuasion_score: int
    improvement: str


@dataclass(frozen=True)
class VisualQaFinding:
    slide_no: int
    category: str
    severity: str
    message: str
    recommendation: str


@dataclass(frozen=True)
class AcceptanceScore:
    customer_ready_score: int
    executive_score: int
    sales_score: int
    technical_score: int
    presentation_score: int
    visual_score: int
    business_value_score: int
    total_score: int


@dataclass(frozen=True)
class HumanAcceptancePrediction:
    no_revision_probability: int
    thirty_min_revision_probability: int
    rationale: list[str]


@dataclass(frozen=True)
class RegressionQuality:
    baseline: str
    improvements: dict[str, int]
    average_improvement_rate: int


@dataclass(frozen=True)
class ProposalValidationResult:
    release_judge: str
    acceptance_scores: AcceptanceScore
    human_acceptance_prediction: HumanAcceptancePrediction
    persona_reviews: list[PersonaReview]
    benchmark_reviews: list[BenchmarkReview]
    red_team_findings: list[RedTeamFinding]
    customer_questions: list[dict[str, str]]
    slide_reviews: list[SlideReview]
    visual_qa_findings: list[VisualQaFinding]
    regression_quality: RegressionQuality
    required_fixes: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_proposal(data: PowerPointData, context: dict[str, Any] | None = None) -> ProposalValidationResult:
    """Evaluate whether a generated proposal is suitable for customer submission."""

    proposal_context = context or {}
    deck_text = _deck_text(data)
    category_scores = _category_scores(data, deck_text, proposal_context)
    visual_findings = _visual_qa(data)
    slide_reviews = _slide_reviews(data)
    red_team = _red_team_findings(category_scores, visual_findings, data)
    judgement_context = {
        **proposal_context,
        "client_name": data.client_name,
        "deck_title": data.deck_title,
    }
    unified_assessment = assess_customer_ready_deck(data.slides, judgement_context, visual_findings=visual_findings)
    acceptance = _acceptance_from_unified_assessment(unified_assessment)
    persona_reviews = _persona_reviews(category_scores, data)
    benchmark_reviews = _benchmark_reviews(category_scores)
    questions = _customer_questions(data, proposal_context)
    regression = _regression_quality(category_scores, acceptance.total_score)
    required_fixes = _required_fixes(red_team, visual_findings, acceptance)
    required_fixes = list(dict.fromkeys([*unified_assessment.required_fixes, *required_fixes]))[:8]
    release_judge = unified_assessment.release_judge
    prediction = _human_acceptance_prediction(acceptance.total_score, release_judge, required_fixes)

    return ProposalValidationResult(
        release_judge=release_judge,
        acceptance_scores=acceptance,
        human_acceptance_prediction=prediction,
        persona_reviews=persona_reviews,
        benchmark_reviews=benchmark_reviews,
        red_team_findings=red_team,
        customer_questions=questions,
        slide_reviews=slide_reviews,
        visual_qa_findings=visual_findings,
        regression_quality=regression,
        required_fixes=required_fixes,
        summary=_summary(release_judge, acceptance.total_score, required_fixes),
    )


def run_golden_validation_suite() -> dict[str, Any]:
    results = []
    for item in _golden_cases():
        validation = validate_proposal(item["powerpoint_data"], item["context"])
        results.append(
            {
                "case_id": item["case_id"],
                "category": item["category"],
                "expected_release_judge": item.get("expected_release_judge") or "CUSTOMER_READY",
                "release_judge": validation.release_judge,
                "total_score": validation.acceptance_scores.total_score,
                "customer_ready_score": validation.acceptance_scores.customer_ready_score,
                "no_revision_probability": validation.human_acceptance_prediction.no_revision_probability,
            }
        )
    average = round(sum(item["total_score"] for item in results) / len(results))
    return {
        "case_count": len(results),
        "average_score": average,
        "customer_ready_count": sum(1 for item in results if item["release_judge"] == "CUSTOMER_READY"),
        "review_required_count": sum(1 for item in results if item["release_judge"] == "REVIEW_REQUIRED"),
        "not_ready_count": sum(1 for item in results if item["release_judge"] == "NOT_READY"),
        "results": results,
    }


def _acceptance_from_unified_assessment(assessment: Any) -> AcceptanceScore:
    scores = assessment_to_acceptance_scores(assessment)
    return AcceptanceScore(
        customer_ready_score=scores["customer_ready_score"],
        executive_score=scores["executive_score"],
        sales_score=scores["sales_score"],
        technical_score=scores["technical_score"],
        presentation_score=scores["presentation_score"],
        visual_score=scores["visual_score"],
        business_value_score=scores["business_value_score"],
        total_score=scores["total_score"],
    )


def _deck_text(data: PowerPointData) -> str:
    parts = [data.deck_title, data.client_name]
    for slide in data.slides:
        parts.extend([slide.title, slide.speaker_notes, slide.visual_suggestion])
        parts.extend(slide.bullets)
    return "\n".join(str(part or "") for part in parts).lower()


def _category_scores(data: PowerPointData, text: str, context: dict[str, Any]) -> dict[str, int]:
    slide_count = len(data.slides)
    story_terms = ["現状", "課題", "原因", "解決", "導入", "効果", "今後", "next", "roadmap", "成功"]
    roi_terms = ["roi", "投資", "費用", "効果", "削減", "売上", "回収", "予算", "kpi", "目標"]
    differentiation_terms = ["差別化", "競合", "勝ち筋", "優位", "比較", "選ばれる", "独自"]
    risk_terms = ["リスク", "懸念", "対策", "セキュリティ", "運用", "教育", "障害", "確認"]
    executive_terms = ["経営", "意思決定", "投資価値", "結論", "期待効果", "サマリー", "executive"]
    technical_terms = ["api", "連携", "システム", "運用", "セキュリティ", "データ", "技術", "保守"]
    visual_terms = ["図", "フロー", "比較", "カード", "タイムライン", "ロードマップ", "kpi", "マトリクス", "before"]
    cta_terms = ["次", "アクション", "合意", "確認", "判断", "打ち合わせ", "提出"]

    scores = {
        "story": _presence_score(text, story_terms, 62, 96),
        "roi": _presence_score(text, roi_terms, 58, 94),
        "differentiation": _presence_score(text, differentiation_terms, 58, 94),
        "risk": _presence_score(text, risk_terms, 55, 92),
        "executive": _presence_score(text, executive_terms, 56, 94),
        "technical": _presence_score(text, technical_terms, 55, 92),
        "visual": _visual_readiness_score(data, visual_terms),
        "cta": _presence_score(text, cta_terms, 58, 94),
        "slide_balance": _slide_balance_score(data),
        "readability": _readability_score(data),
    }
    if slide_count >= 8:
        scores["story"] = min(100, scores["story"] + 4)
        scores["slide_balance"] = min(100, scores["slide_balance"] + 5)
    if str(context.get("decision_maker") or context.get("persona") or "").strip():
        scores["executive"] = min(100, scores["executive"] + 3)
    return scores


def _presence_score(text: str, terms: list[str], floor: int, ceiling: int) -> int:
    hits = sum(1 for term in terms if term.lower() in text)
    return _clamp(floor + hits * 5, 0, ceiling)


def _visual_readiness_score(data: PowerPointData, terms: list[str]) -> int:
    if not data.slides:
        return 0
    visual_hits = 0
    for slide in data.slides:
        visual = f"{slide.layout} {slide.visual_suggestion}".lower()
        if any(term.lower() in visual for term in terms):
            visual_hits += 1
    ratio = visual_hits / len(data.slides)
    return _clamp(round(58 + ratio * 40), 0, 98)


def _slide_balance_score(data: PowerPointData) -> int:
    if not data.slides:
        return 0
    layouts = [slide.layout for slide in data.slides]
    repeated = sum(1 for index in range(2, len(layouts)) if layouts[index] == layouts[index - 1] == layouts[index - 2])
    ideal = 8 <= len(data.slides) <= 18
    score = 88 if ideal else 72
    return _clamp(score - repeated * 8, 0, 100)


def _readability_score(data: PowerPointData) -> int:
    if not data.slides:
        return 0
    penalties = 0
    for slide in data.slides:
        if len(slide.title) > 42:
            penalties += 5
        if len(slide.bullets) > 6:
            penalties += 7
        if sum(len(item) for item in slide.bullets) > 380:
            penalties += 8
    return _clamp(94 - penalties, 0, 100)


def _persona_reviews(scores: dict[str, int], data: PowerPointData) -> list[PersonaReview]:
    return [
        _persona("営業部長", round((scores["differentiation"] + scores["roi"] + scores["cta"]) / 3), ["勝ち筋", "価格妥当性", "受注確度"]),
        _persona("営業マネージャー", round((scores["story"] + scores["readability"] + scores["cta"]) / 3), ["説明順", "次アクション", "修正量"]),
        _persona("営業担当", round((scores["readability"] + scores["risk"] + scores["story"]) / 3), ["説明しやすさ", "質問対応", "不足情報"]),
        _persona("顧客経営者", round((scores["executive"] + scores["roi"] + scores["story"]) / 3), ["投資価値", "経営メリット", "意思決定材料"]),
        _persona("顧客情報システム", round((scores["technical"] + scores["risk"] + scores["readability"]) / 3), ["技術実現性", "運用", "セキュリティ"]),
        _persona("顧客現場責任者", round((scores["risk"] + scores["readability"] + scores["cta"]) / 3), ["現場運用", "教育", "導入負荷"]),
    ]


def _persona(persona: str, score: int, criteria: list[str]) -> PersonaReview:
    verdict = "提出可能" if score >= 84 else "軽微な確認が必要" if score >= 72 else "修正が必要"
    concerns = [] if score >= 84 else [f"{criteria[0]}の根拠をもう一段明確にしてください。"]
    fixes = [] if score >= 84 else [f"{persona}が気にする「{criteria[1]}」を1スライド内で補足してください。"]
    return PersonaReview(
        persona=persona,
        score=score,
        verdict=verdict,
        thoughts=[f"{criteria[0]}、{criteria[1]}、{criteria[2]}を中心に確認します。"],
        strengths=[f"{criteria[0]}の説明が一定水準で整理されています。"],
        concerns=concerns,
        required_fixes=fixes,
    )


def _benchmark_reviews(scores: dict[str, int]) -> list[BenchmarkReview]:
    base = round((scores["story"] + scores["readability"] + scores["differentiation"] + scores["visual"]) / 4)
    reviews = []
    for index, name in enumerate(CONSULTING_BENCHMARKS):
        score = _clamp(base - (index % 3) + 1, 0, 100)
        reviews.append(
            BenchmarkReview(
                benchmark=name,
                score=score,
                structure=scores["slide_balance"],
                story=scores["story"],
                readability=scores["readability"],
                persuasion=round((scores["roi"] + scores["differentiation"]) / 2),
                notes=[
                    "特定企業の資料を模倣せず、一般的なコンサル提案書の品質軸で評価しています。",
                    "結論、根拠、意思決定材料、次アクションの明瞭さを重視しています。",
                ],
            )
        )
    return reviews


def _red_team_findings(scores: dict[str, int], visual_findings: list[VisualQaFinding], data: PowerPointData) -> list[RedTeamFinding]:
    checks = [
        ("roi", "ROI説明が弱い", "投資判断の材料が不足し、価格交渉で不利になります。", "現状値、目標値、測定方法を明記してください。"),
        ("differentiation", "競合との差別化が弱い", "なぜこの提案を選ぶべきかが伝わりにくくなります。", "想定競合、勝ち筋、確認事項を分けて提示してください。"),
        ("risk", "導入リスクの説明が弱い", "情報システム部門や現場責任者の不安が残ります。", "運用、教育、セキュリティ、障害時対応を補足してください。"),
        ("story", "ストーリーの流れが弱い", "読み手が結論にたどり着く前に離脱する可能性があります。", "現状、課題、原因、解決策、効果、今後の順で再整理してください。"),
        ("cta", "次アクションが弱い", "商談後に前へ進む合意が取りにくくなります。", "次回確認事項、合意事項、判断期限を明記してください。"),
    ]
    findings = []
    for key, issue, impact, improvement in checks:
        if scores[key] < 75:
            findings.append(RedTeamFinding("high" if scores[key] < 68 else "medium", issue, impact, improvement))
    if any(item.severity == "critical" for item in visual_findings):
        findings.append(
            RedTeamFinding(
                "critical",
                "視覚品質に重大な懸念があります",
                "文字量や図解不足により、顧客提出時の第一印象が下がります。",
                "文字量を減らし、比較図、KPIカード、ロードマップへ置き換えてください。",
            )
        )
    if len(data.slides) < 6:
        findings.append(
            RedTeamFinding("high", "意思決定に必要なページ数が不足しています", "背景、ROI、リスク、次アクションを説明しきれません。", "最低8ページ程度の構成へ拡張してください。")
        )
    return findings


def _visual_qa(data: PowerPointData) -> list[VisualQaFinding]:
    findings: list[VisualQaFinding] = []
    previous_layouts: list[str] = []
    for slide in data.slides:
        text_length = sum(len(item) for item in slide.bullets)
        visual_text = f"{slide.layout} {slide.visual_suggestion}".lower()
        slide_text = f"{slide.title} {slide.visual_suggestion} " + " ".join(slide.bullets)
        if len(slide.title) > 44:
            findings.append(_visual(slide, "title_length", "medium", "タイトルが長く、結論が伝わりにくい可能性があります。", "32文字前後の結論タイトルへ短縮してください。"))
        if len(slide.bullets) > 7:
            findings.append(_visual(slide, "bullet_count", "high", "箇条書きが多く、説明時に読み上げ資料に見えます。", "要点を3〜5件に絞り、図解やカードに分割してください。"))
        if text_length > 450:
            findings.append(_visual(slide, "text_volume", "critical", "本文量が多く、顧客が短時間で理解しにくい状態です。", "圧縮、分割、図解化のいずれかを行ってください。"))
        if not slide.visual_suggestion.strip():
            findings.append(_visual(slide, "diagram_missing", "medium", "図解方針が不足しています。", "比較図、フロー、タイムライン、KPIカードなどの表現を指定してください。"))
        if slide.visual_suggestion.strip() and not _contains(visual_text, ["カード", "図", "フロー", "比較", "タイムライン", "ロードマップ", "kpi", "マトリクス", "アイコン"]):
            findings.append(_visual(slide, "visual_type_unclear", "medium", "視覚表現の種類が曖昧です。", "カード、比較図、フロー、タイムラインなど、描画形式を明記してください。"))
        if _contains(slide_text, ["比較", "競合", "before", "after"]) and not _contains(visual_text, ["比較", "カード", "マトリクス", "before"]):
            findings.append(_visual(slide, "comparison_visual_missing", "medium", "比較内容に対して比較用の見せ方が不足しています。", "表ではなく比較カード、Before/After、2列マトリクスで見せてください。"))
        if _contains(slide_text, ["kpi", "roi", "目標", "%", "削減", "効果"]) and not _contains(visual_text, ["kpi", "カード", "ダッシュボード", "グラフ"]):
            findings.append(_visual(slide, "kpi_visual_missing", "medium", "数値・効果説明に対してKPIカードやグラフ方針が不足しています。", "現状値、目標値、測定方法をカードまたは簡易グラフで表示してください。"))
        if _contains(slide_text, ["スケジュール", "工程", "導入", "ロードマップ", "フェーズ"]) and not _contains(visual_text, ["タイムライン", "ロードマップ", "ガント"]):
            findings.append(_visual(slide, "timeline_visual_missing", "medium", "導入時期や工程に対して時間軸の表現が不足しています。", "ロードマップまたはガントチャート風の表示にしてください。"))
        if text_length > 300 and len(slide.bullets) >= 5 and not _contains(visual_text, ["カード", "分割", "図"]):
            findings.append(_visual(slide, "whitespace_risk", "medium", "本文量に対して余白不足になりやすい構成です。", "1ページ1メッセージに絞り、カード分割またはスライド分割を検討してください。"))
        if slide.visual_suggestion.strip() and not _contains(visual_text, ["アイコン", "icon"]):
            findings.append(_visual(slide, "icon_guidance_missing", "low", "アイコン利用方針が明記されていません。", "課題、効果、リスク、アクションの意味が伝わる統一アイコンを指定してください。"))
        if len(slide.title) < 8 and len(slide.bullets) >= 4:
            findings.append(_visual(slide, "headline_weak", "medium", "タイトルが短すぎてページの結論が伝わりにくい可能性があります。", "単語タイトルではなく、読み手が判断できる結論タイトルにしてください。"))
        previous_layouts.append(slide.layout)
        if len(previous_layouts) >= 3 and previous_layouts[-1] == previous_layouts[-2] == previous_layouts[-3]:
            findings.append(_visual(slide, "layout_repetition", "medium", "同じレイアウトが3ページ連続しています。", "比較、カード、ロードマップなどへレイアウトを切り替えてください。"))
    return findings


def _visual(slide: PowerPointSlide, category: str, severity: str, message: str, recommendation: str) -> VisualQaFinding:
    return VisualQaFinding(slide.slide_no, category, severity, message, recommendation)


def _slide_reviews(data: PowerPointData) -> list[SlideReview]:
    reviews = []
    for slide in data.slides:
        text_length = sum(len(item) for item in slide.bullets)
        has_conclusion = any(term in slide.title for term in ["結論", "提案", "効果", "解決", "次", "ROI", "KPI", "成功", "勝ち筋"]) or len(slide.title) <= 34
        volume = "多い" if text_length > 380 or len(slide.bullets) > 6 else "少ない" if text_length < 70 else "適正"
        readability = _clamp(92 - max(0, len(slide.bullets) - 5) * 7 - max(0, text_length - 360) // 20, 0, 100)
        design = 86 if slide.visual_suggestion.strip() else 68
        persuasion = _clamp(round((readability + design + (90 if has_conclusion else 70)) / 3), 0, 100)
        improvement = "顧客提出可能な水準です。" if persuasion >= 84 else "結論タイトル、要点圧縮、図解方針の明記を行ってください。"
        reviews.append(SlideReview(slide.slide_no, slide.title, has_conclusion, volume, readability, design, persuasion, improvement))
    return reviews


def _customer_questions(data: PowerPointData, context: dict[str, Any]) -> list[dict[str, str]]:
    client = data.client_name or "お客様"
    base = [
        ("価格が高い理由は何ですか？", "費用の内訳を必須、推奨、オプションに分け、投資対効果とリスク低減効果で説明します。"),
        ("競合との差は何ですか？", "単なる機能比較ではなく、課題理解、導入後の運用、改善サイクルまで含めた勝ち筋で説明します。"),
        ("導入期間はどのくらいですか？", "要件確認、初期構築、検証、運用開始の段階に分け、判断ポイントを明確にします。"),
        ("ROIの根拠は何ですか？", "現状時間、削減対象、単価、対象件数を確認し、PoCで目標値を確定する前提で説明します。"),
        ("既存システム連携は可能ですか？", "API、CSV、運用手順のいずれで接続するかを確認し、段階的に検証します。"),
        ("AI精度は保証できますか？", "初期段階では保証ではなく目標値を設定し、学習データと検証結果で判断します。"),
        ("セキュリティ面は問題ありませんか？", "利用データ、保管範囲、権限、ログ、外部連携の確認項目を整理して合意します。"),
        ("保守体制はどうなりますか？", "運用開始後の問い合わせ、障害対応、改善提案の役割分担を明確にします。"),
        ("現場教育は必要ですか？", "新しい運用が入る場合は、担当者向けの短時間トレーニングと手順書を用意します。"),
        ("障害時はどうしますか？", "代替運用、手動戻し、連絡先、復旧基準を事前に定義します。"),
        ("社内承認に必要な資料はありますか？", "経営向けサマリー、ROI、リスク、スケジュール、概算費用を1セットで整理します。"),
        ("PoCと本番導入の違いは何ですか？", "PoCは実現性と効果確認、本番は運用設計、連携、教育、保守を含みます。"),
        ("追加費用が発生する条件は？", "対象範囲、データ量、連携方式、追加機能、運用支援の有無で変動します。"),
        ("導入後の成果はどう測りますか？", "KPIを現状値、目標値、測定方法、測定タイミングで定義します。"),
        ("現場負荷は増えませんか？", "初期は確認作業が発生しますが、標準化と自動化で総作業時間を下げる設計にします。"),
        ("どこまで自動化できますか？", "完全自動化ではなく、人が判断すべき箇所を残して安全に効率化します。"),
        ("導入しない場合のリスクは？", "属人化、処理遅延、品質ばらつき、機会損失が継続する点を説明します。"),
        ("契約前に確認すべきことは？", "対象範囲、成功条件、スケジュール、費用、役割分担、データ提供条件です。"),
        ("誰が意思決定すべきですか？", "経営、部門責任者、情報システム、現場責任者の合意が必要です。"),
        ("次に何をすればよいですか？", f"{client}側の確認事項を整理し、次回打ち合わせでPoC範囲と評価基準を合意します。"),
    ]
    return [{"question": question, "answer": answer} for question, answer in base]


def _regression_quality(scores: dict[str, int], total: int) -> RegressionQuality:
    improvements = {
        "story": _improvement(scores["story"]),
        "roi": _improvement(scores["roi"]),
        "winning_strategy": _improvement(scores["differentiation"]),
        "kpi": _improvement(round((scores["roi"] + scores["technical"]) / 2)),
        "estimate": _improvement(round((scores["roi"] + scores["readability"]) / 2)),
        "executive_summary": _improvement(scores["executive"]),
        "beautiful_ai": _improvement(scores["visual"]),
        "ppt": _improvement(round((scores["visual"] + scores["slide_balance"]) / 2)),
        "quality_gate": _improvement(round((scores["risk"] + scores["readability"]) / 2)),
        "customer_ready": _improvement(total),
    }
    return RegressionQuality("Version2.0 quality baseline", improvements, round(sum(improvements.values()) / len(improvements)))


def _improvement(score: int) -> int:
    return _clamp(round((score - 65) * 1.4), 0, 45)


def _required_fixes(red_team: list[RedTeamFinding], visual_findings: list[VisualQaFinding], acceptance: AcceptanceScore) -> list[str]:
    fixes = [item.improvement for item in red_team if item.severity in {"critical", "high"}]
    fixes.extend(item.recommendation for item in visual_findings if item.severity == "critical")
    if acceptance.total_score < 85 and not fixes:
        fixes.append("ROI、競合差別化、次アクションのいずれかを補強してください。")
    return list(dict.fromkeys(fixes))[:8]


def _human_acceptance_prediction(total: int, judge: str, fixes: list[str]) -> HumanAcceptancePrediction:
    no_revision = _clamp(total + (5 if judge == "CUSTOMER_READY" else -8) - len(fixes) * 2, 0, 99)
    within_thirty = _clamp(no_revision + 10 + min(10, len(fixes) * 2), 0, 99)
    return HumanAcceptancePrediction(
        no_revision_probability=no_revision,
        thirty_min_revision_probability=within_thirty,
        rationale=[
            "提出可否スコア、重大指摘数、修正必要項目数から推定しています。",
            "30分以内修正確率は、軽微な追記で解消できる指摘を含めて算出しています。",
        ],
    )


def _summary(judge: str, total: int, fixes: list[str]) -> str:
    if judge == "CUSTOMER_READY":
        return f"総合{total}点。営業担当者が顧客へ提出可能な水準です。"
    if judge == "REVIEW_REQUIRED":
        return f"総合{total}点。提出前に{max(1, len(fixes))}件の確認を推奨します。"
    return f"総合{total}点。顧客提出前に重要な修正が必要です。"


def _golden_cases() -> list[dict[str, Any]]:
    categories = [
        "Web制作",
        "EC",
        "AI",
        "DX",
        "建設",
        "製造",
        "物流",
        "教育",
        "自治体",
        "医療",
        "採用",
        "マーケティング",
        "SaaS",
        "小売",
        "BtoB",
        "BtoC",
        "スタートアップ",
        "中小企業",
        "大企業",
        "官公庁",
    ]
    ready = [_golden_case(index + 1, category) for index, category in enumerate(categories[:8])]
    review = [_golden_review_case(index + 9, category) for index, category in enumerate(categories[8:15])]
    not_ready = [_golden_not_ready_case(index + 16, category) for index, category in enumerate(categories[15:20])]
    return ready + review + not_ready


def _golden_case(case_no: int, category: str) -> dict[str, Any]:
    slides = [
        _slide(1, "Executive Summary: 結論と期待効果", ["現状課題、解決策、期待効果、投資価値を2分で理解できる構成です。", "ROI、KPI、次アクションを明確にします。"], "hero", "カードUIとKPIカード"),
        _slide(2, "現状と課題", ["現状、課題、原因を分けて整理します。", "属人化、処理遅延、品質ばらつきを確認します。"], "problem", "課題マップ"),
        _slide(3, "勝ち筋と差別化", ["想定競合、勝ち筋、差別化、確認事項を整理します。", "価格だけでなく運用支援と成果測定で差別化します。"], "comparison", "比較カード"),
        _slide(4, "提案する解決策", [f"{category}向けに段階導入し、現場負荷を抑えます。", "API、運用、教育、保守まで含めます。"], "solution", "Before After フロー"),
        _slide(5, "KPIとROI設計", ["現状値、目標値、測定方法、測定タイミング、担当を定義します。", "投資対効果と削減時間を合意します。"], "kpi", "KPIダッシュボード"),
        _slide(6, "導入ロードマップ", ["要件確認、PoC、検証、本番導入、運用改善の順で進めます。", "各フェーズに判断ポイントを置きます。"], "timeline", "ロードマップ"),
        _slide(7, "リスクと対策", ["セキュリティ、運用、教育、障害時、データ連携のリスクを管理します。", "確認事項を事前に合意します。"], "risk", "リスクマトリクス"),
        _slide(8, "概算見積と次アクション", ["必須、推奨、オプションを分けて説明します。", "次回は範囲、予算、意思決定者を確認します。"], "estimate", "見積カードとCTA"),
    ]
    data = PowerPointData(deck_title=f"{category}向け顧客提出提案書", client_name=f"{category}サンプル企業", slides=slides)
    return {"case_id": f"golden-{case_no:02d}", "category": category, "powerpoint_data": data, "context": {"industry": category, "decision_maker": "経営者"}}


def _golden_review_case(case_no: int, category: str) -> dict[str, Any]:
    slides = [
        _slide(1, "Executive Summary", ["current issue and proposed direction are summarized"], "hero", "summary panel"),
        _slide(2, "Current issue", ["main business issue and root cause are partially described"], "problem", "issue list"),
        _slide(3, "Proposal direction", ["solution approach and implementation scope are described"], "proposal", "simple flow"),
        _slide(4, "Expected value", ["effect and KPI are mentioned but measurement owner is not fixed"], "content", "value cards"),
        _slide(5, "Schedule", ["roadmap and next meeting are described at a high level"], "timeline", "timeline"),
        _slide(6, "Risk note", ["risk and confirmation items need sales review"], "risk", "risk list"),
    ]
    data = PowerPointData(deck_title=f"{category} review-required proposal", client_name=f"{category} review sample", slides=slides)
    return {
        "case_id": f"golden-{case_no:02d}",
        "category": category,
        "expected_release_judge": "REVIEW_REQUIRED",
        "powerpoint_data": data,
        "context": {"industry": category, "decision_maker": "Department Manager"},
    }


def _golden_not_ready_case(case_no: int, category: str) -> dict[str, Any]:
    slides = [
        PowerPointSlide(
            slide_no=1,
            layout="title_body",
            title="Info",
            bullets=[
                "No customer name, no ROI basis, no risk plan, no next action, no schedule, no estimate, and no evidence. "
                * 10
            ],
            speaker_notes="",
            visual_suggestion="",
        )
    ]
    data = PowerPointData(deck_title=f"{category} insufficient proposal", client_name="Client", slides=slides)
    return {
        "case_id": f"golden-{case_no:02d}",
        "category": category,
        "expected_release_judge": "NOT_READY",
        "powerpoint_data": data,
        "context": {"industry": category, "decision_maker": ""},
    }


def _slide(no: int, title: str, bullets: list[str], layout: str, visual: str) -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=no,
        layout=layout,
        title=title,
        bullets=bullets,
        speaker_notes="顧客の意思決定に必要な根拠、リスク、次アクションを説明します。",
        visual_suggestion=visual,
    )


def _clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


def _contains(text: str, keywords: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(keyword.lower() in lowered for keyword in keywords)
