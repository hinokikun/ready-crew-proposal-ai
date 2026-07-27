from app.models import PowerPointSlide
from app.services.presentation_designer_ai import LAYOUT_LIBRARY, analyze_layout_decisions, classify_slide_type


def make_slide(slide_no: int, title: str, bullets: list[str], layout: str = "Title + Body") -> PowerPointSlide:
    return PowerPointSlide(
        slide_no=slide_no,
        title=title,
        bullets=bullets,
        layout=layout,
        speaker_notes="",
        visual_suggestion="",
    )


def test_layout_library_has_required_ids() -> None:
    ids = {layout.id for layout in LAYOUT_LIBRARY}
    assert len(ids) >= 17
    assert {"LAYOUT-001", "LAYOUT-006", "LAYOUT-007", "LAYOUT-008", "LAYOUT-009", "LAYOUT-017"}.issubset(ids)


def test_layout_selection_uses_slide_type_and_content_signals() -> None:
    slides = [
        make_slide(1, "表紙", ["AI画像認識導入支援"], "Title Only"),
        make_slide(2, "Before / After", ["Beforeは人手確認、AfterはAI候補提示と人の最終承認で比較します"], "Title + Body"),
        make_slide(3, "KPI・評価基準", ["候補正答率、確認時間、修正率をPoCで評価します"], "Title + Body"),
        make_slide(4, "導入スケジュール", ["要件定義、検証、現場適用をフェーズごとに進めます"], "Title + Body"),
        make_slide(5, "次のアクション", ["画像サンプルと評価基準を確認します"], "Title + Body"),
    ]
    decisions = analyze_layout_decisions(slides, template="data_driven", story_type="AI導入", audience="品質保証", presentation_score=72)

    assert decisions[0].recommended_layout.name == "Hero"
    assert decisions[1].recommended_layout.name == "Comparison Table"
    assert decisions[2].recommended_layout.name in {"KPI Cards", "Large Number"}
    assert decisions[3].recommended_layout.name in {"Timeline", "Roadmap"}
    assert all(decision.score_after >= decision.score_before for decision in decisions)


def test_variation_prevents_three_identical_layouts() -> None:
    slides = [make_slide(index + 1, f"課題 {index + 1}", ["課題と対応を整理します"], "Title + Body") for index in range(4)]
    decisions = analyze_layout_decisions(slides, presentation_score=68)

    triples = zip(decisions, decisions[1:], decisions[2:])
    assert all(len({a.recommended_layout.id, b.recommended_layout.id, c.recommended_layout.id}) > 1 for a, b, c in triples)


def test_template_design_tokens_are_template_specific() -> None:
    slide = make_slide(1, "表紙", ["提案テーマ"], "Title Only")
    dark = analyze_layout_decisions([slide], template="modern_dark")[0]
    minimal = analyze_layout_decisions([slide], template="executive_minimal")[0]

    assert dark.design_token.color_role != minimal.design_token.color_role
    assert dark.design_token.spacing == "generous"
    assert minimal.design_token.body_size == 17


def test_slide_type_classifier_covers_required_examples() -> None:
    assert classify_slide_type(make_slide(1, "表紙", ["提案"], "Hero"), index=0, total_slides=8) == "Cover"
    assert classify_slide_type(make_slide(2, "現状課題", ["課題があります"], "Title + Body"), index=1, total_slides=8) == "Problem"
    assert classify_slide_type(make_slide(3, "競合比較", ["A案とB案を比較"], "Title + Body"), index=2, total_slides=8) == "Comparison"
    assert classify_slide_type(make_slide(4, "ロードマップ", ["段階導入"], "Title + Body"), index=3, total_slides=8) == "Roadmap"
    assert classify_slide_type(make_slide(5, "見積", ["費用"], "Title + Body"), index=4, total_slides=8) == "Estimate"
    assert classify_slide_type(make_slide(8, "次のアクション", ["承認"], "Checklist"), index=7, total_slides=8) == "Next Action"
