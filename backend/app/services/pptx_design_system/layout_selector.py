from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import PowerPointSlide, PresentationLayoutDecisionContract
from app.services.pptx_parts.models import PptxContext

from .design_tokens import tokens_for_template
from .diagram_primitives import primitive_for_text
from .typography import text_density_score


@dataclass(frozen=True)
class LayoutCatalogItem:
    layout_id: str
    name: str
    purpose: str
    visual: str


CORE_LAYOUT_CATALOG: tuple[LayoutCatalogItem, ...] = (
    LayoutCatalogItem("LAYOUT-001", "Title Only", "強いメッセージのみを伝える", "headline"),
    LayoutCatalogItem("LAYOUT-002", "Title + Body", "短い説明と補助図を並べる", "body_visual"),
    LayoutCatalogItem("LAYOUT-003", "Two Column", "2つの観点を比較する", "two_column"),
    LayoutCatalogItem("LAYOUT-004", "Three Column", "3つの要点を整理する", "three_column"),
    LayoutCatalogItem("LAYOUT-005", "Hero Cover", "表紙で提案の主役を示す", "hero"),
    LayoutCatalogItem("LAYOUT-006", "KPI Cards", "指標や評価観点をカード化する", "kpi_cards"),
    LayoutCatalogItem("LAYOUT-007", "Comparison Cards", "現状・課題・目指す姿を比較する", "comparison"),
    LayoutCatalogItem("LAYOUT-008", "Timeline", "時系列の流れを示す", "timeline"),
    LayoutCatalogItem("LAYOUT-009", "Roadmap", "段階導入や意思決定を示す", "roadmap"),
    LayoutCatalogItem("LAYOUT-010", "Flow", "処理や業務の流れを示す", "flow"),
    LayoutCatalogItem("LAYOUT-011", "Matrix", "2軸で優先度を示す", "matrix"),
    LayoutCatalogItem("LAYOUT-012", "Quote", "重要な一文を強調する", "quote"),
    LayoutCatalogItem("LAYOUT-013", "Image Left", "差し替え可能なビジュアルを左に置く", "image_left"),
    LayoutCatalogItem("LAYOUT-014", "Image Right", "差し替え可能なビジュアルを右に置く", "image_right"),
    LayoutCatalogItem("LAYOUT-015", "Large Number", "主要数値を強調する", "large_number"),
    LayoutCatalogItem("LAYOUT-016", "Checklist", "確認事項を整理する", "checklist"),
    LayoutCatalogItem("LAYOUT-017", "Closing", "次の行動を明確にする", "closing"),
    LayoutCatalogItem("LAYOUT-018", "Executive Message", "経営者向けに結論を先に伝える", "executive_message"),
    LayoutCatalogItem("LAYOUT-019", "Current State Map", "現状と影響を構造化する", "current_state"),
    LayoutCatalogItem("LAYOUT-020", "Problem Structure", "症状・原因・根本原因を示す", "issue_tree"),
    LayoutCatalogItem("LAYOUT-021", "Before After Transformation", "現状から目指す姿への変化を示す", "before_after"),
    LayoutCatalogItem("LAYOUT-022", "Strategic Options", "選択肢と推奨案を説明する", "options"),
    LayoutCatalogItem("LAYOUT-023", "Value Proposition", "顧客価値を段階化して示す", "value"),
    LayoutCatalogItem("LAYOUT-024", "KPI Design Dashboard", "SMART形式でKPIを設計する", "kpi_dashboard"),
    LayoutCatalogItem("LAYOUT-025", "ROI Logic", "投資と効果の考え方を示す", "roi_bridge"),
    LayoutCatalogItem("LAYOUT-026", "Competitive Positioning", "競合に対する位置取りを示す", "positioning"),
    LayoutCatalogItem("LAYOUT-027", "Layered Architecture", "システムや業務のレイヤーを示す", "architecture"),
    LayoutCatalogItem("LAYOUT-028", "Workstream Roadmap", "作業工程と意思決定を示す", "workstream"),
    LayoutCatalogItem("LAYOUT-029", "Risk Heatmap", "リスクと対策優先度を示す", "risk"),
    LayoutCatalogItem("LAYOUT-030", "Governance Map", "体制と責任分担を示す", "governance"),
    LayoutCatalogItem("LAYOUT-031", "Cost Breakdown", "費用を必須・推奨・任意で説明する", "cost"),
    LayoutCatalogItem("LAYOUT-032", "Scope Definition", "提案範囲と対象外を明確化する", "scope"),
    LayoutCatalogItem("LAYOUT-033", "Section Divider", "章の転換を印象づける", "section"),
)

_V4_LAYOUT_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    ("Executive Decision Brief", "結論と判断材料を1枚で示す", "executive"),
    ("CEO Two-Minute Summary", "経営層が短時間で判断できる構成にする", "executive"),
    ("Situation Complication Resolution", "背景・変化・解決策をSCRで示す", "scr"),
    ("Recommendation Proof Stack", "推奨案と根拠を縦方向に接続する", "proof_stack"),
    ("Insight Headline Canvas", "強い示唆を大きく見せる", "insight"),
    ("One Message Evidence Pair", "1メッセージと1根拠に絞る", "assertion_evidence"),
    ("Issue Tree", "課題を原因構造へ分解する", "issue_tree"),
    ("Root Cause Map", "根本原因と影響を結びつける", "root_cause"),
    ("MECE Buckets", "論点を重複なく整理する", "mece"),
    ("Problem Impact Bridge", "課題と事業影響を橋渡しする", "impact_bridge"),
    ("Before After Bridge", "現状から目指す姿への変化を示す", "before_after"),
    ("Current Future Map", "現在と将来像を対比する", "current_future"),
    ("Transformation Path", "変革の移行ステップを示す", "transformation"),
    ("Value Proposition Pyramid", "価値を経営・業務・実行へ階層化する", "pyramid"),
    ("Benefit Ladder", "便益が積み上がる構造を示す", "ladder"),
    ("Strategic Options Matrix", "選択肢と推奨案を比較する", "options_matrix"),
    ("Decision Matrix", "意思決定軸ごとに評価する", "decision_matrix"),
    ("Competitive Positioning Map", "競合に対する位置取りを示す", "positioning"),
    ("Differentiation Radar", "差別化要素を視覚化する", "radar"),
    ("Win Theme Canvas", "勝ち筋を顧客価値に変換する", "win_theme"),
    ("KPI Executive Dashboard", "KPIをダッシュボード化する", "kpi_dashboard"),
    ("KPI Gauge Board", "指標の状態と測定方針をゲージで示す", "kpi_gauge"),
    ("SMART KPI Canvas", "現状・目標・測定・判定を整理する", "smart_kpi"),
    ("ROI Dashboard", "投資と効果を一目で示す", "roi_dashboard"),
    ("ROI Waterfall", "投資回収の流れを段階表示する", "roi_waterfall"),
    ("Payback Logic", "回収条件と判断基準を示す", "payback"),
    ("Roadmap Swimlane", "作業・成果物・判断をレーンで示す", "swimlane"),
    ("Implementation Timeline", "導入工程を時系列で示す", "timeline"),
    ("Milestone Roadmap", "重要な節目と意思決定を示す", "milestone"),
    ("Phase Gate Plan", "フェーズごとの合意点を示す", "phase_gate"),
    ("Process Flow", "処理や業務の流れを示す", "process"),
    ("Operating Model", "人・業務・システムの役割を示す", "operating_model"),
    ("Customer Journey", "顧客体験の流れを示す", "journey"),
    ("Service Blueprint", "表側と裏側の業務を分けて示す", "blueprint"),
    ("Architecture Stack", "構成要素をレイヤー化する", "architecture"),
    ("Platform Blueprint", "基盤・連携・運用を示す", "platform"),
    ("Data Flow Map", "データの流れと戻りループを示す", "data_flow"),
    ("Integration Map", "既存システム連携を示す", "integration"),
    ("Capability Map", "必要機能を能力単位で整理する", "capability"),
    ("Business Model Canvas", "事業モデルの構成を示す", "business_model"),
    ("Value Chain", "価値連鎖のどこを改善するか示す", "value_chain"),
    ("Organization Map", "体制と役割分担を示す", "organization"),
    ("Governance Triangle", "意思決定・実行・支援を接続する", "governance"),
    ("RACI Snapshot", "責任分担を簡潔に示す", "raci"),
    ("Risk Radar", "主要リスクを影響度で示す", "risk_radar"),
    ("Risk Heatmap", "リスクと対策優先度を示す", "risk_heatmap"),
    ("Mitigation Plan", "対策方針と確認方法を示す", "mitigation"),
    ("Cost Tiering", "必須・推奨・任意で費用を説明する", "cost_tiering"),
    ("Investment Mix", "投資配分と判断余地を示す", "investment_mix"),
    ("Estimate Range", "概算レンジと条件を示す", "estimate_range"),
    ("Scope Map", "対象・対象外・前提を整理する", "scope"),
    ("Scope Boundary", "提案範囲の境界を明確化する", "boundary"),
    ("Next Meeting Plan", "次回打ち合わせで合意する内容を示す", "next_meeting"),
    ("Action Commitment", "次アクションと責任を示す", "action"),
    ("Closing Decision Page", "意思決定へ向けた締めを作る", "closing"),
    ("Case Study Snapshot", "実績を短く証拠化する", "case_study"),
    ("Proof Points", "判断根拠を短く並べる", "proof"),
    ("Evidence Tiles", "証拠を種類別に整理する", "evidence"),
    ("Market Context", "市場背景と緊急性を示す", "market"),
    ("Industry Forces", "業界課題を構造化する", "industry"),
    ("Customer Pain Map", "顧客課題を可視化する", "pain_map"),
    ("Stakeholder Map", "関係者と関心を示す", "stakeholder"),
    ("Decision Maker Lens", "決裁者の見方で整理する", "decision_maker"),
    ("Objection Response", "想定反論と回答を示す", "objection"),
    ("FAQ Cluster", "主要質問を論点別にまとめる", "faq"),
    ("Assumption Ledger", "前提・仮説・確認事項を分ける", "assumption"),
    ("Numeric Integrity Board", "数値の前提と確認方法を示す", "numeric"),
    ("Quality Review Canvas", "提出前の確認観点を整理する", "quality"),
    ("Visual QA Snapshot", "見た目の確認結果を示す", "visual_qa"),
    ("Executive Scorecard", "経営判断に必要な評価を示す", "scorecard"),
    ("Sales Talk Track", "営業説明の順番を示す", "talk_track"),
    ("Customer Outcome Map", "顧客が得る成果を示す", "outcome"),
    ("Success Image", "導入後の成功状態を示す", "success"),
    ("Change Management Map", "定着に必要な施策を示す", "change"),
    ("Adoption Curve", "利用定着の進み方を示す", "adoption"),
    ("Training Plan", "教育と移行を示す", "training"),
    ("Operations Loop", "運用改善の循環を示す", "ops_loop"),
    ("Learning Loop", "ログから改善する流れを示す", "learning"),
    ("AI Human Collaboration", "AIと人の役割分担を示す", "ai_human"),
    ("Automation Scope", "自動化対象と人の確認を分ける", "automation"),
    ("Technology Fit", "技術適合性を示す", "technology"),
    ("Security Control Map", "セキュリティ対策を示す", "security"),
    ("Compliance Checklist", "遵守事項を確認する", "compliance"),
    ("Implementation Readiness", "導入準備度を示す", "readiness"),
    ("Pilot Design", "PoC範囲と評価基準を示す", "pilot"),
    ("Pilot Evaluation Board", "PoCの合否判断を示す", "evaluation"),
    ("Rollout Plan", "本番展開の流れを示す", "rollout"),
    ("Appendix Divider", "補足資料への切り替えを示す", "appendix"),
    ("Reference Page", "補足根拠を整理する", "reference"),
)

V4_CONSULTING_LAYOUT_CATALOG: tuple[LayoutCatalogItem, ...] = tuple(
    LayoutCatalogItem(f"LAYOUT-{index:03d}", name, purpose, visual)
    for index, (name, purpose, visual) in enumerate(_V4_LAYOUT_DEFINITIONS, start=34)
)

LAYOUT_CATALOG: tuple[LayoutCatalogItem, ...] = (*CORE_LAYOUT_CATALOG, *V4_CONSULTING_LAYOUT_CATALOG)

CATALOG_BY_ID = {item.layout_id: item for item in LAYOUT_CATALOG}


def create_consulting_layout_decisions(
    slides: list[PowerPointSlide],
    context: PptxContext,
    *,
    template: str,
    summary_mode: bool,
) -> list[PresentationLayoutDecisionContract]:
    tokens = tokens_for_template(template, summary_mode=summary_mode)
    decisions: list[PresentationLayoutDecisionContract] = []
    recent: list[str] = []
    for index, slide in enumerate(slides, start=1):
        slide_type = consulting_slide_type(slide, index=index, context=context)
        candidates = candidate_layouts_for_slide(slide, slide_type, summary_mode=summary_mode)
        selected = _avoid_repetition(candidates, recent)
        recent.append(selected)
        if len(recent) > 3:
            recent.pop(0)
        decisions.append(
            PresentationLayoutDecisionContract(
                slide_id=f"consulting-v4-slide-{index}",
                slide_index=index,
                slide_type=slide_type,
                selected_layout_id=selected,
                recommended_layout_ids=candidates,
                selection_reason=_selection_reason(slide, slide_type, selected),
                expected_effect=_expected_effect(selected),
                template_id=template,
                design_token_id=tokens.token_id,
                applied_by="quality_engine",
                status="applied",
                confidence=0.88,
                human_review_required=False,
            )
        )
    return decisions


def consulting_slide_type(slide: PowerPointSlide, *, index: int, context: PptxContext) -> str:
    text = _slide_text(slide)
    title = slide.title or ""
    if index == 1 or slide.layout == "title":
        return "Cover"
    if re.search(r"勝ち筋|差別化|競合|比較|選定|市場", title):
        return "Competitive Positioning"
    if re.search(r"懸念|回答|反論|FAQ|リスク|対策|セキュリティ", title):
        return "Risk"
    if re.search(r"KPI|指標|測定|目標|ROI|投資|効果|削減|費用対効果", title, re.IGNORECASE):
        return "KPI" if re.search(r"KPI|指標|測定|目標", title, re.IGNORECASE) else "ROI"
    if re.search(r"スケジュール|ロードマップ|フェーズ|Phase|工程|導入", title, re.IGNORECASE):
        return "Roadmap"
    if re.search(r"現状|現在|背景|業務|理解", title):
        return "Current State"
    if re.search(r"課題|原因|要因|ボトルネック", title):
        return "Problem Structure"
    if re.search(r"Before|After|改善後|目指す姿|現状と", title, re.IGNORECASE):
        return "Before After"
    if re.search(r"ジャーニー|導線|流れ", title):
        return "Journey"
    if re.search(r"サイトマップ|構成|アーキテクチャ|連携|システム", title, re.IGNORECASE):
        return "Architecture"
    if re.search(r"戦略|方針|コンテンツ|ターゲット|ユーザー", title):
        return "Strategy"
    if re.search(r"見積|費用|概算|予算|必須|推奨|オプション|万円", title):
        return "Cost"
    if re.search(r"今後|次回|アクション|確認事項|進め方", title):
        return "Next Action"
    if re.search(r"経営層|結論|Executive|サマリー|要点|期待効果|提案サマリー", title, re.IGNORECASE):
        return "Executive Summary"
    if re.search(r"現状|現在|背景|業務", text):
        return "Current State"
    if re.search(r"課題|原因|要因|ボトルネック", text):
        return "Problem Structure"
    if re.search(r"Before|After|改善後|目指す姿|現状と", text, re.IGNORECASE):
        return "Before After"
    if re.search(r"競合|差別化|勝ち筋|比較|選定", text):
        return "Competitive Positioning"
    if re.search(r"KPI|指標|測定|目標|現状値|目標値", text, re.IGNORECASE):
        return "KPI"
    if re.search(r"ROI|投資|効果|削減|費用対効果", text, re.IGNORECASE):
        return "ROI"
    if re.search(r"API|CSV|連携|システム|構成|アーキテクチャ|AI|OCR", text, re.IGNORECASE):
        return "Architecture"
    if re.search(r"スケジュール|ロードマップ|フェーズ|Phase|工程|導入", text, re.IGNORECASE):
        return "Roadmap"
    if re.search(r"リスク|懸念|対策|セキュリティ", text):
        return "Risk"
    if re.search(r"体制|役割|責任|PM|チーム", text, re.IGNORECASE):
        return "Governance"
    if re.search(r"見積|費用|概算|予算|必須|推奨|オプション|万円", text):
        return "Cost"
    if re.search(r"範囲|対象外|スコープ", text):
        return "Scope"
    if re.search(r"今後|次回|アクション|確認事項|進め方", text):
        return "Next Action"
    if len(title) <= 16 and not slide.bullets:
        return "Section Divider"
    return "Recommendation"


def candidate_layouts_for_slide(slide: PowerPointSlide, slide_type: str, *, summary_mode: bool) -> list[str]:
    text = _slide_text(slide)
    density = text_density_score(slide.title, slide.bullets)
    base = {
        "Cover": ["LAYOUT-005"],
        "Executive Summary": ["LAYOUT-034", "LAYOUT-036", "LAYOUT-037"],
        "Current State": ["LAYOUT-045", "LAYOUT-046", "LAYOUT-040"],
        "Problem Structure": ["LAYOUT-040", "LAYOUT-041", "LAYOUT-042"],
        "Before After": ["LAYOUT-044", "LAYOUT-045", "LAYOUT-046"],
        "Competitive Positioning": ["LAYOUT-051", "LAYOUT-052", "LAYOUT-053"],
        "KPI": ["LAYOUT-054", "LAYOUT-055", "LAYOUT-056"],
        "ROI": ["LAYOUT-057", "LAYOUT-058", "LAYOUT-059"],
        "Architecture": ["LAYOUT-070", "LAYOUT-071", "LAYOUT-072"],
        "Roadmap": ["LAYOUT-060", "LAYOUT-061", "LAYOUT-062"],
        "Risk": ["LAYOUT-080", "LAYOUT-081", "LAYOUT-082"],
        "Governance": ["LAYOUT-077", "LAYOUT-078", "LAYOUT-079"],
        "Cost": ["LAYOUT-083", "LAYOUT-084", "LAYOUT-085"],
        "Scope": ["LAYOUT-086", "LAYOUT-087", "LAYOUT-099"],
        "Next Action": ["LAYOUT-088", "LAYOUT-089", "LAYOUT-090"],
        "Journey": ["LAYOUT-066", "LAYOUT-060", "LAYOUT-044"],
        "Strategy": ["LAYOUT-047", "LAYOUT-053", "LAYOUT-042"],
        "Section Divider": ["LAYOUT-033", "LAYOUT-001"],
        "Recommendation": ["LAYOUT-037", "LAYOUT-047", "LAYOUT-049", "LAYOUT-053", "LAYOUT-034"],
    }.get(slide_type, ["LAYOUT-037", "LAYOUT-047", "LAYOUT-002"])
    if density > 72 and base[0] not in {"LAYOUT-040", "LAYOUT-070", "LAYOUT-060"}:
        base = ["LAYOUT-086", *base]
    primitive = primitive_for_text(text)
    if primitive == "issue_tree" and "LAYOUT-040" not in base:
        base = ["LAYOUT-040", *base]
    if primitive == "layered_architecture" and "LAYOUT-070" not in base:
        base = ["LAYOUT-070", *base]
    if summary_mode:
        base = [layout for layout in base if layout not in {"LAYOUT-031", "LAYOUT-032"}] or base
    return _unique_layouts(base)


def _avoid_repetition(candidates: list[str], recent: list[str]) -> str:
    if len(recent) < 2 or not (recent[-1] == recent[-2] == candidates[0]):
        return candidates[0]
    for candidate in candidates[1:]:
        if candidate != recent[-1]:
            return candidate
    fallback_cycle = ["LAYOUT-034", "LAYOUT-040", "LAYOUT-044", "LAYOUT-054", "LAYOUT-057", "LAYOUT-060", "LAYOUT-070", "LAYOUT-080", "LAYOUT-083", "LAYOUT-088"]
    for candidate in fallback_cycle:
        if candidate != recent[-1]:
            return candidate
    return candidates[0]


def _selection_reason(slide: PowerPointSlide, slide_type: str, layout_id: str) -> str:
    item = CATALOG_BY_ID.get(layout_id)
    purpose = item.purpose if item else "顧客向けに読みやすい構造へ変換"
    return f"{slide_type}として、{purpose}ため。本文量、数値、比較、リスク、工程情報をもとに選択しました。"


def _expected_effect(layout_id: str) -> str:
    item = CATALOG_BY_ID.get(layout_id)
    if not item:
        return "1ページ1メッセージと視線誘導を改善します。"
    return f"{item.name}により、{item.purpose}表現へ整えます。"


def _slide_text(slide: PowerPointSlide) -> str:
    return "\n".join([slide.title, slide.visual_suggestion, *slide.bullets])


def _unique_layouts(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
