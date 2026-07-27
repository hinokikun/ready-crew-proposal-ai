"""Synthetic Deck Blueprint fixtures for Phase 1.5."""

from __future__ import annotations

import copy
from typing import Any, Dict, List


SECTION_SEQUENCE = [
    ("sec-cover", "cover", "表紙", "提案の主題を提示する"),
    ("sec-summary", "executive_summary", "要約", "意思決定に必要な結論を先に示す"),
    ("sec-problem", "problem", "課題", "顧客課題を共有する"),
    ("sec-insight", "insight", "示唆", "課題から提案方針へ接続する"),
    ("sec-solution", "solution", "提案", "解決策を提示する"),
    ("sec-kpi", "kpi", "評価基準", "成果の測定方法を示す"),
    ("sec-roadmap", "roadmap", "進め方", "導入手順を示す"),
    ("sec-pricing", "pricing", "概算費用", "価値と費用の関係を示す"),
    ("sec-risk", "risk", "リスク", "懸念と対策を示す"),
    ("sec-next", "next_action", "次のアクション", "意思決定後の行動を明確にする"),
]

SLIDE_TYPES = {
    "cover": ("opening", "cover", "cover", "hook"),
    "executive_summary": ("summary", "executive_summary", "executive_summary", "frame"),
    "problem": ("problem", "problem_statement", "problem_sharing", "diagnose"),
    "insight": ("insight", "recommended_strategy", "customer_insight", "explain"),
    "solution": ("recommendation", "proposal_overview", "proposal_overview", "recommend"),
    "kpi": ("proof", "kpi_definition", "kpi_definition", "quantify"),
    "roadmap": ("plan", "roadmap", "roadmap", "explain"),
    "pricing": ("decision", "estimate_overview", "pricing", "quantify"),
    "risk": ("support", "risk_register", "risk_handling", "de_risk"),
    "next_action": ("closing", "next_action", "next_action", "ask"),
}


def _section(section_id: str, section_type: str, title: str, goal: str, order: int, slide_id: str) -> Dict[str, Any]:
    return {
        "section_id": section_id,
        "section_type": section_type,
        "section_title": title,
        "section_goal": goal,
        "section_order": order,
        "required": True,
        "minimum_slides": 1,
        "maximum_slides": 3,
        "slide_ids": [slide_id],
        "entry_message": f"{title}を確認します。",
        "exit_message": f"{title}から次の論点へ進みます。",
        "transition_type": "continue",
        "decision_relevance": "high" if section_type in {"executive_summary", "pricing", "next_action"} else "medium",
    }


def _slide(order: int, section_id: str, section_type: str, title: str, theme: str) -> Dict[str, Any]:
    slide_role, slide_type, slide_goal, narrative_function = SLIDE_TYPES[section_type]
    slide_id = f"slide-{theme}-{order:02d}"
    return {
        "slide_order": order,
        "slide_role": slide_role,
        "slide_type": slide_type,
        "section_id": section_id,
        "slide_goal": slide_goal,
        "narrative_function": narrative_function,
        "working_title": title,
        "key_message": f"{title}を通じて、提案判断に必要な情報を整理します。",
        "required": True,
        "optional": False,
        "decision_relevance": "high" if section_type in {"executive_summary", "pricing", "next_action"} else "medium",
        "evidence_requirement": "balanced",
        "transition_from_previous": "continue" if order > 0 else "none",
        "transition_to_next": "summary_to_action" if section_type == "next_action" else "continue",
        "slide_blueprint_id": slide_id,
    }


def _ref(slide: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "slide_blueprint_id": slide["slide_blueprint_id"],
        "slide_id": slide["slide_blueprint_id"],
        "slide_order": slide["slide_order"],
        "expected_slide_type": slide["slide_type"],
        "expected_slide_goal": slide["slide_goal"],
        "section_id": slide["section_id"],
        "required": slide["required"],
        "embedded_slide_blueprint": None,
    }


def _base_deck(theme: str, title: str, *, deck_type: str = "sales_proposal", story_arc: str = "problem_solution", seniority: str = "senior_manager") -> Dict[str, Any]:
    sections = []
    slides = []
    for order, (section_id, section_type, section_title, section_goal) in enumerate(SECTION_SEQUENCE):
        slide = _slide(order, section_id, section_type, section_title, theme)
        sections.append(_section(section_id, section_type, section_title, section_goal, order, slide["slide_blueprint_id"]))
        slides.append(slide)
    return {
        "deck_blueprint_version": "pe2_deck_blueprint_v1",
        "deck_id": f"deck-{theme}",
        "project_id": f"project-{theme}",
        "deck_title": title,
        "deck_type": deck_type,
        "status": "validated",
        "language": "ja",
        "created_at": "2026-07-27T00:00:00Z",
        "deck_goal": "sell",
        "primary_audience": "department_head",
        "audience_seniority": seniority,
        "decision_stage": "approval",
        "decision_question": "この提案を次の検討段階へ進めるべきか",
        "desired_decision": "PoCまたは次回打ち合わせへ進む判断を得る",
        "desired_reaction": "課題、価値、進め方が明確で検討しやすいと感じる",
        "decision_urgency": "normal",
        "story_arc": story_arc,
        "persuasion_strategy": "roi",
        "evidence_strategy": "balanced",
        "core_thesis": "現状課題を整理し、段階的な導入でリスクを抑えながら成果を確認する。",
        "value_proposition": "業務時間の削減と品質の標準化を同時に実現する。",
        "key_differentiator": "AI活用と人の判断を組み合わせた現場定着型の提案である。",
        "primary_objection": "導入負荷と費用対効果が不明確ではないか",
        "objection_response": {
            "objection_id": "obj-roi",
            "objection": "費用対効果が不明確",
            "response": "PoCで評価指標を確認し、本番判断の根拠を作ります。",
            "evidence_requirement": "balanced",
            "related_slide_ids": [slides[5]["slide_blueprint_id"], slides[7]["slide_blueprint_id"]],
        },
        "sections": sections,
        "slide_plan": slides,
        "target_slide_count": len(slides),
        "minimum_slide_count": 8,
        "maximum_slide_count": 14,
        "deck_length_type": "standard",
        "appendix_allowed": True,
        "optional_sections": ["faq", "appendix"],
        "required_sections": ["cover", "executive_summary", "problem", "solution", "kpi", "roadmap", "pricing", "next_action"],
        "opening_message": "本提案の目的と判断ポイントを最初に共有します。",
        "problem_statement": "現状の業務には工数、品質、判断材料の不足という課題があります。",
        "insight_statement": "課題は単独ではなく、業務フローと判断基準の設計に関係しています。",
        "recommendation_statement": "段階的なPoCで価値と運用適合性を確認することを推奨します。",
        "impact_statement": "確認時間、品質、意思決定速度の改善が期待できます。",
        "closing_message": "次回は対象範囲と評価基準を確定します。",
        "narrative_summary": "課題を共有し、示唆から提案へ接続し、評価基準と費用を確認したうえで次の行動を決める構成です。",
        "story_beats": [
            {"beat_id": "beat-hook", "narrative_function": "hook", "message": "提案テーマを明確にする", "related_section_ids": ["sec-cover"], "related_slide_ids": [slides[0]["slide_blueprint_id"]]},
            {"beat_id": "beat-diagnose", "narrative_function": "diagnose", "message": "課題を整理する", "related_section_ids": ["sec-problem"], "related_slide_ids": [slides[2]["slide_blueprint_id"]]},
            {"beat_id": "beat-recommend", "narrative_function": "recommend", "message": "提案方針を示す", "related_section_ids": ["sec-solution"], "related_slide_ids": [slides[4]["slide_blueprint_id"]]},
            {"beat_id": "beat-ask", "narrative_function": "ask", "message": "次の行動を合意する", "related_section_ids": ["sec-next"], "related_slide_ids": [slides[9]["slide_blueprint_id"]]},
        ],
        "key_takeaways": ["課題が明確", "PoCで確認可能", "次の行動が具体的"],
        "decision_points": [
            {"decision_id": "dec-poc", "question": "PoCへ進むか", "required_evidence": ["評価基準", "概算費用"], "related_slide_ids": [slides[5]["slide_blueprint_id"], slides[7]["slide_blueprint_id"]], "urgency": "normal"}
        ],
        "approval_requirements": [
            {"requirement_id": "app-budget", "approver": "部門責任者", "approval_condition": "PoC範囲と概算費用の合意", "related_slide_ids": [slides[7]["slide_blueprint_id"]]}
        ],
        "cta_plan": {
            "cta_strategy": "次回打ち合わせでPoC条件を確定する",
            "next_action": "対象範囲と評価基準を確認する",
            "owner": "営業担当",
            "due_timing": "次回打ち合わせ",
            "success_condition": "PoC実施可否の判断材料が揃う",
        },
        "next_action": "対象範囲と評価基準を確認する",
        "risk_level": "medium",
        "decision_dependencies": ["評価基準", "対象範囲", "概算費用"],
        "theme_direction": {
            "recommended_theme": "consulting",
            "tone": "consulting",
            "formality": "business",
            "visual_density": "medium",
            "evidence_density": "balanced",
            "executive_summary_required": True,
        },
        "slide_blueprint_refs": [_ref(slide) for slide in slides],
        "generation_source": "offline_fixture",
        "confidence": 0.84,
        "warnings": [],
        "validation_result": None,
        "evaluation_result": None,
        "source_references": [{"source_id": "src-training", "label": "研修用架空案件", "source_type": "fixture", "confidence": "high"}],
        "created_by": "phase1_5_fixture",
        "schema_version": "pe2_deck_blueprint_v1",
        "audience_profile": {
            "primary_audience": "department_head",
            "seniority": seniority,
            "decision_stage": "approval",
            "known_priorities": ["費用対効果", "実行可能性"],
            "avoid_topics": ["根拠のない断定"],
        },
        "constraints": [{"constraint_id": "con-no-facts", "label": "未入力の事実を作らない", "detail": "数値は入力またはPoC測定と明記する", "blocking": True}],
        "transitions": [
            {"transition_type": "continue", "from_slide_id": slides[index]["slide_blueprint_id"], "to_slide_id": slides[index + 1]["slide_blueprint_id"], "bridge_message": "次の論点へ進みます。"}
            for index in range(len(slides) - 1)
        ],
    }


VALID_CASES = [
    ("web_agency", "Web制作会社向け新規サイト提案", "web_production_proposal", "problem_solution", "senior_manager"),
    ("saas_intro", "SaaS導入提案", "saas_introduction", "why_what_how", "senior_manager"),
    ("ai_efficiency", "AI業務効率化提案", "consulting_proposal", "diagnosis_strategy_execution", "senior_manager"),
    ("competitive_pitch", "競合プレゼン提案", "competitive_pitch", "insight_recommendation", "executive"),
    ("executive", "経営層向け投資判断提案", "executive_proposal", "executive_decision", "executive"),
    ("field", "現場責任者向け運用改善提案", "project_plan", "current_future", "field_leader"),
    ("new_sales", "新規営業提案", "sales_proposal", "problem_solution", "manager"),
    ("renewal", "更新提案", "renewal_proposal", "current_future", "senior_manager"),
    ("training", "社内研修資料提案", "internal_approval", "why_what_how", "manager"),
    ("consulting", "コンサルティング提案", "consulting_proposal", "diagnosis_strategy_execution", "executive"),
    ("short5", "短縮版5枚提案", "sales_proposal", "executive_decision", "executive"),
    ("standard10", "標準10枚提案", "sales_proposal", "problem_solution", "senior_manager"),
    ("detailed15", "詳細15枚提案", "consulting_proposal", "diagnosis_strategy_execution", "senior_manager"),
    ("roi", "ROI重視提案", "investment_pitch", "executive_decision", "executive"),
    ("pricing", "価格重視提案", "sales_proposal", "opportunity_solution_impact", "senior_manager"),
    ("case", "実績重視提案", "sales_proposal", "insight_recommendation", "manager"),
    ("roadmap", "ロードマップ重視提案", "project_plan", "current_future", "field_leader"),
    ("comparison", "比較重視提案", "competitive_pitch", "insight_recommendation", "executive"),
    ("ec", "ECサイト改善提案", "web_production_proposal", "opportunity_solution_impact", "manager"),
    ("hr", "採用サイト提案", "web_production_proposal", "problem_solution", "senior_manager"),
    ("dx", "営業DX提案", "consulting_proposal", "why_what_how", "executive"),
    ("knowledge", "社内ナレッジ検索提案", "saas_introduction", "diagnosis_strategy_execution", "senior_manager"),
    ("crm", "CRM導入提案", "saas_introduction", "current_future", "senior_manager"),
    ("ocr", "AI-OCR導入提案", "consulting_proposal", "problem_solution", "manager"),
]


def _adjust_short(deck: Dict[str, Any]) -> Dict[str, Any]:
    keep_sections = {"sec-cover", "sec-summary", "sec-problem", "sec-solution", "sec-kpi", "sec-roadmap", "sec-pricing", "sec-next"}
    deck["sections"] = [section for section in deck["sections"] if section["section_id"] in keep_sections]
    deck["slide_plan"] = [slide for slide in deck["slide_plan"] if slide["section_id"] in keep_sections]
    for order, slide in enumerate(deck["slide_plan"]):
        slide["slide_order"] = order
    deck["slide_blueprint_refs"] = [_ref(slide) for slide in deck["slide_plan"]]
    deck["target_slide_count"] = len(deck["slide_plan"])
    deck["minimum_slide_count"] = 5
    deck["maximum_slide_count"] = 8
    deck["deck_length_type"] = "short"
    return deck


def _adjust_detailed(deck: Dict[str, Any]) -> Dict[str, Any]:
    theme = deck["deck_id"].replace("deck-", "")
    appendix_slide = _slide(len(deck["slide_plan"]), "sec-appendix", "next_action", "補足", theme)
    appendix_slide.update({"slide_role": "appendix", "slide_type": "appendix", "slide_goal": "appendix", "narrative_function": "explain"})
    appendix_slide_2 = _slide(len(deck["slide_plan"]) + 1, "sec-appendix", "next_action", "技術補足", theme)
    appendix_slide_2.update({"slide_role": "appendix", "slide_type": "appendix", "slide_goal": "appendix", "narrative_function": "explain"})
    appendix = _section("sec-appendix", "appendix", "補足", "詳細条件を補足する", len(deck["sections"]), appendix_slide["slide_blueprint_id"])
    appendix["slide_ids"].append(appendix_slide_2["slide_blueprint_id"])
    appendix["maximum_slides"] = 4
    deck["sections"].append(appendix)
    deck["slide_plan"].append(appendix_slide)
    deck["slide_plan"].append(appendix_slide_2)
    deck["slide_blueprint_refs"] = [_ref(slide) for slide in deck["slide_plan"]]
    deck["target_slide_count"] = len(deck["slide_plan"])
    deck["minimum_slide_count"] = 10
    deck["maximum_slide_count"] = 25
    deck["deck_length_type"] = "detailed"
    return deck


def valid_deck_payloads() -> List[Dict[str, Any]]:
    decks: List[Dict[str, Any]] = []
    for theme, title, deck_type, story_arc, seniority in VALID_CASES:
        deck = _base_deck(theme, title, deck_type=deck_type, story_arc=story_arc, seniority=seniority)
        if theme == "short5":
            deck = _adjust_short(deck)
        if theme == "detailed15":
            deck = _adjust_detailed(deck)
        decks.append(deck)
    return decks


def golden_deck_payloads() -> List[Dict[str, Any]]:
    return valid_deck_payloads()[:12]


def invalid_deck_payloads() -> List[Dict[str, Any]]:
    base = _base_deck("invalid-base", "異常系ベース提案")
    invalid: List[Dict[str, Any]] = []

    no_cover = copy.deepcopy(base)
    no_cover["sections"] = no_cover["sections"][1:]
    invalid.append(no_cover)

    no_next = copy.deepcopy(base)
    no_next["sections"] = no_next["sections"][:-1]
    invalid.append(no_next)

    price_first = copy.deepcopy(base)
    price_first["sections"][7]["section_order"] = 0
    price_first["sections"][0]["section_order"] = 7
    invalid.append(price_first)

    bad_section_order = copy.deepcopy(base)
    bad_section_order["sections"][2]["section_order"] = bad_section_order["sections"][3]["section_order"]
    invalid.append(bad_section_order)

    duplicate_slide_order = copy.deepcopy(base)
    duplicate_slide_order["slide_plan"][1]["slide_order"] = duplicate_slide_order["slide_plan"][0]["slide_order"]
    invalid.append(duplicate_slide_order)

    broken_section_ref = copy.deepcopy(base)
    broken_section_ref["sections"][2]["slide_ids"] = ["missing-slide"]
    invalid.append(broken_section_ref)

    executive_missing_summary = copy.deepcopy(base)
    executive_missing_summary["audience_seniority"] = "executive"
    executive_missing_summary["sections"] = [section for section in executive_missing_summary["sections"] if section["section_type"] != "executive_summary"]
    invalid.append(executive_missing_summary)

    placeholder = copy.deepcopy(base)
    placeholder["deck_title"] = "TBD"
    invalid.append(placeholder)

    missing_refs = copy.deepcopy(base)
    missing_refs["slide_blueprint_refs"] = []
    invalid.append(missing_refs)

    ref_mismatch = copy.deepcopy(base)
    ref_mismatch["slide_blueprint_refs"][0]["expected_slide_type"] = "faq"
    invalid.append(ref_mismatch)

    cta_missing = copy.deepcopy(base)
    cta_missing["next_action"] = ""
    cta_missing["cta_plan"]["next_action"] = ""
    invalid.append(cta_missing)

    invalid_enum = copy.deepcopy(base)
    invalid_enum["deck_type"] = "not_a_deck_type"
    invalid.append(invalid_enum)

    return invalid
