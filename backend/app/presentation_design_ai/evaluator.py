"""Report extractors for Presentation Design AI artifacts."""

from __future__ import annotations

from .density_optimizer import visible_character_count
from .models import DesignDeck
from .validators import has_repeated_composition


def information_architecture_report(deck: DesignDeck) -> dict:
    return deck.information_architecture.to_dict()


def narrative_flow_report(deck: DesignDeck) -> dict:
    return {
        "case_id": deck.case_id,
        "slide_count": deck.slide_count,
        "title_only_story": [contract.action_title for contract in deck.slide_contracts],
        "connections": [
            {
                "slide_id": contract.slide_id,
                "previous": contract.previous_slide_connection,
                "next": contract.next_slide_transition,
            }
            for contract in deck.slide_contracts
        ],
    }


def diagram_selection_report(deck: DesignDeck) -> dict:
    return {
        "case_id": deck.case_id,
        "slides": [
            {
                "slide_id": contract.slide_id,
                "diagram_type": contract.diagram_type,
                "selected_diagram": contract.diagram_decision.selected_diagram,
                "rejected_candidates": contract.diagram_decision.rejected_candidates,
                "selection_reason": contract.diagram_decision.selection_reason,
                "required_evidence": contract.diagram_decision.required_evidence,
                "visual_risk": contract.diagram_decision.visual_risk,
                "fallback_diagram": contract.diagram_decision.fallback_diagram,
                "diagram_required": contract.diagram_decision.diagram_required,
                "necessity_reason": contract.diagram_decision.necessity_reason,
            }
            for contract in deck.slide_contracts
        ],
    }


def visual_hierarchy_report(deck: DesignDeck) -> dict:
    return {
        "case_id": deck.case_id,
        "slides": [
            {
                "slide_id": contract.slide_id,
                "composition_type": contract.composition_type,
                "composition_family": contract.composition_family,
                "dominant_visual": contract.dominant_visual,
                "typography_mode": contract.typography_mode,
                "photography_mode": contract.photography_mode,
                "whitespace_strategy": contract.whitespace_strategy,
                "red_semantic": contract.red_semantic,
                "dark_mass_usage": contract.dark_mass_usage,
                "composition_selection_reason": contract.composition_selection_reason,
                "priority": contract.information_priority,
                "reading_order": contract.reading_order,
                "focal_point": contract.focal_point,
                "secondary_point": contract.secondary_point,
            }
            for contract in deck.slide_contracts
        ],
        "repeated_composition": has_repeated_composition(deck),
    }


def quality_retention_report(deck: DesignDeck) -> dict:
    slides = []
    generic_escapes = []
    for contract in deck.slide_contracts:
        retention = contract.quality_retention
        selected = contract.diagram_decision.selected_diagram
        generic_escape = _is_generic_escape(contract)
        if generic_escape:
            generic_escapes.append(contract.slide_id)
        slides.append(
            {
                "slide_id": contract.slide_id,
                "source_item": contract.source_basis[0] if contract.source_basis else "",
                "core_message": retention.core_message,
                "business_object": retention.business_object,
                "decision_role": retention.decision_role,
                "dominant_visual_intent": retention.dominant_visual_intent,
                "required_business_evidence": retention.required_business_evidence,
                "editorial_temperature": retention.editorial_temperature,
                "must_preserve_semantic_relationship": retention.must_preserve_semantic_relationship,
                "selected_diagram": selected,
                "generic_diagram_escape": generic_escape,
                "dominant_visual_strength": _dominant_visual_strength(contract),
                "business_object_retention": _business_object_retention(contract),
                "decision_role_retention": _decision_role_retention(contract),
                "anchor_principle_retention": _anchor_principle_retention(contract),
            }
        )
    return {
        "case_id": deck.case_id,
        "quality_retention_score": round(sum(item["anchor_principle_retention"] for item in slides) / max(1, len(slides)), 3),
        "generic_diagram_escape_count": len(generic_escapes),
        "generic_diagram_escape_slides": generic_escapes,
        "deck_art_direction_repetition": deck_art_direction_repetition(deck),
        "slides": slides,
    }


def visual_specificity_report(deck: DesignDeck) -> dict:
    slides = []
    for contract in deck.slide_contracts:
        rectangle_dependency = _rectangle_dependency_score(contract)
        card_dependency = _card_dependency_score(contract)
        visual_specificity = _visual_specificity_score(contract, rectangle_dependency, card_dependency)
        slides.append(
            {
                "slide_id": contract.slide_id,
                "source_item": contract.source_basis[0] if contract.source_basis else "",
                "business_object": contract.quality_retention.business_object,
                "visual_representation_candidates": _visual_representation_candidates(contract),
                "selected_visual_representation": _selected_visual_representation(contract),
                "photography_decision": _photography_decision(contract),
                "rectangle_dependency_score": rectangle_dependency,
                "card_dependency_score": card_dependency,
                "visual_specificity_score": visual_specificity,
                "strong_visual_moment": visual_specificity >= 0.75 and _dominant_visual_strength(contract) >= 0.72,
            }
        )
    return {
        "case_id": deck.case_id,
        "visual_specificity_score": round(sum(item["visual_specificity_score"] for item in slides) / max(1, len(slides)), 3),
        "rectangle_dependency_score": round(sum(item["rectangle_dependency_score"] for item in slides) / max(1, len(slides)), 3),
        "card_dependency_score": round(sum(item["card_dependency_score"] for item in slides) / max(1, len(slides)), 3),
        "photography_decision_coverage": round(
            sum(1 for item in slides if item["photography_decision"] in {"required", "helpful", "unnecessary"})
            / max(1, len(slides)),
            3,
        ),
        "strong_visual_moment_count": sum(1 for item in slides if item["strong_visual_moment"]),
        "slides": slides,
    }


def meaning_to_visual_report(deck: DesignDeck) -> dict:
    slides = []
    for contract in deck.slide_contracts:
        source_item = contract.source_basis[0] if contract.source_basis else ""
        slides.append(
            {
                "slide_id": contract.slide_id,
                "source_item": source_item,
                "core_message": contract.quality_retention.core_message,
                "business_object": contract.quality_retention.business_object,
                "decision_role": contract.quality_retention.decision_role,
                "visual_metaphor": _visual_metaphor(contract),
                "visual_subject": _visual_subject(contract),
                "visual_tension": _visual_tension(contract),
                "visual_hierarchy": _visual_hierarchy_path(contract),
                "visual_entry_point": _visual_entry_point(contract),
                "visual_exit_point": _visual_exit_point(contract),
                "human_attention_path": _human_attention_path(contract),
                "three_second_comprehension": _three_second_comprehension(contract, source_item),
                "three_second_gate": "PASS" if _three_second_gate(contract, source_item) else "REVIEW",
            }
        )
    pass_count = sum(1 for item in slides if item["three_second_gate"] == "PASS")
    return {
        "case_id": deck.case_id,
        "three_second_pass_count": pass_count,
        "three_second_pass_ratio": round(pass_count / max(1, len(slides)), 3),
        "slides": slides,
    }


def deck_art_direction_repetition(deck: DesignDeck) -> dict:
    backgrounds = [_background_temperature(contract) for contract in deck.slide_contracts]
    visual_mass = [contract.dark_mass_usage for contract in deck.slide_contracts]
    typography = [contract.typography_mode for contract in deck.slide_contracts]
    density = [contract.text_density_target for contract in deck.slide_contracts]
    return {
        "background_temperature_repetition": _repeats_three(backgrounds),
        "visual_mass_repetition": _repeats_three([value for value in visual_mass if value != "avoid_as_default_anchor"]),
        "typography_scale_repetition": _repeats_three(typography),
        "density_repetition": _repeats_three(density),
        "photography_frequency": sum(1 for contract in deck.slide_contracts if contract.photography_mode != "none"),
        "editorial_tension_slides": sum(1 for contract in deck.slide_contracts if contract.quality_retention.editorial_temperature in {"fracture / loss", "judgment pressure", "specific tension"}),
    }


def content_density_report(deck: DesignDeck) -> dict:
    counts = [
        visible_character_count(contract.action_title, contract.core_message, contract.takeaway, *contract.supporting_evidence)
        for contract in deck.slide_contracts
    ]
    return {
        "case_id": deck.case_id,
        "average_visible_characters": round(sum(counts) / max(1, len(counts)), 1),
        "max_visible_characters": max(counts) if counts else 0,
        "diagram_ratio_average": round(sum(contract.diagram_ratio_target for contract in deck.slide_contracts) / max(1, deck.slide_count), 3),
        "slides": [
            {
                "slide_id": contract.slide_id,
                "visible_characters": count,
                "target": contract.text_density_target,
                "diagram_ratio_target": contract.diagram_ratio_target,
                "diagram_required": contract.diagram_decision.diagram_required,
            }
            for contract, count in zip(deck.slide_contracts, counts)
        ],
    }


def human_designer_review(deck: DesignDeck) -> dict:
    findings = []
    for contract in deck.slide_contracts:
        count = visible_character_count(contract.action_title, contract.core_message, contract.takeaway, *contract.supporting_evidence)
        if count > 150:
            findings.append(
                {
                    "slide_id": contract.slide_id,
                    "finding": "Visible copy may still feel dense.",
                    "suggested_fix": "Move supporting evidence to notes or change to a more visual composition.",
                }
            )
        if contract.composition_type in {"three_column", "comparison"} and contract.diagram_ratio_target < 0.68:
            findings.append(
                {
                    "slide_id": contract.slide_id,
                    "finding": "This could become a card-only page if not inspected.",
                    "suggested_fix": "Confirm that diagram shape, arrows, and focal point are visible in rendered PNG.",
                }
            )
    if not findings:
        findings.append(
            {
                "slide_id": "deck",
                "finding": "No mechanical design issue detected.",
                "suggested_fix": "Human should inspect contact sheet rhythm and business nuance.",
            }
        )
    return {"case_id": deck.case_id, "findings": findings}


def _is_generic_escape(contract) -> bool:
    generic_diagrams = {
        "step_flow",
        "process_flow",
        "generic_flowchart",
        "timeline",
        "phased_roadmap",
        "comparison_matrix",
        "current_future_table",
        "kpi_dashboard",
        "progress_meter",
        "funnel",
        "matrix",
    }
    has_specific_object = contract.quality_retention.business_object not in {"customer business object", "customer business context"}
    selected = contract.diagram_decision.selected_diagram
    if has_specific_object and selected in generic_diagrams:
        return True
    if contract.source_basis and contract.source_basis[0] == "roi" and selected in {"step_flow", "process_flow", "kpi_dashboard", "progress_meter"}:
        return True
    return False


def _dominant_visual_strength(contract) -> float:
    score = 0.58
    if "hero" in contract.quality_retention.editorial_temperature or contract.typography_mode == "typography_as_visual_anchor":
        score += 0.18
    if contract.photography_mode == "meaningful_business_object":
        score += 0.12
    if contract.dark_mass_usage != "avoid_as_default_anchor":
        score += 0.06
    if "generic" in contract.diagram_decision.selected_diagram:
        score -= 0.2
    return round(min(1.0, max(0.0, score)), 3)


def _business_object_retention(contract) -> float:
    object_text = contract.quality_retention.business_object.lower()
    if any(
        word in object_text
        for word in (
            "decision record",
            "target image",
            "flower",
            "judgment",
            "reason",
            "threshold",
            "readiness",
            "site",
            "conversion",
            "content",
            "candidate",
            "screening",
            "defect",
            "inspection",
            "quality",
        )
    ):
        return 1.0
    if contract.diagram_decision.selected_diagram in {"process_flow", "step_flow", "timeline"}:
        return 0.35
    return 0.72


def _decision_role_retention(contract) -> float:
    role = contract.quality_retention.decision_role.lower()
    if any(word in role for word in ("decision", "go", "approval", "start", "threshold", "judgment")):
        return 1.0
    return 0.72


def _anchor_principle_retention(contract) -> float:
    if _is_generic_escape(contract):
        return 0.35
    return round((_dominant_visual_strength(contract) + _business_object_retention(contract) + _decision_role_retention(contract)) / 3, 3)


def _visual_representation_candidates(contract) -> tuple[str, str, str]:
    object_text = contract.quality_retention.business_object.lower()
    if any(word in object_text for word in ("site", "conversion", "content")):
        return ("website/interface crop", "brand-commerce editorial surface", "customer path decision surface")
    if any(word in object_text for word in ("defect", "inspection", "quality")):
        return ("inspection evidence crop", "quality gate surface", "exception trail")
    if any(word in object_text for word in ("candidate", "screening", "recruiter")):
        return ("candidate dossier", "interview handoff journey", "responsibility boundary surface")
    if any(word in object_text for word in ("flower", "target image")):
        return ("annotated evidence image", "decision record", "quality judgment surface")
    return ("editorial evidence surface", "decision surface", "typographic metaphor")


def _selected_visual_representation(contract) -> str:
    candidates = _visual_representation_candidates(contract)
    if contract.photography_mode == "meaningful_business_object":
        return candidates[0]
    if contract.dark_mass_usage != "avoid_as_default_anchor":
        return candidates[1]
    return candidates[2]


def _photography_decision(contract) -> str:
    object_text = contract.quality_retention.business_object.lower()
    if any(word in object_text for word in ("flower", "target image", "site", "conversion", "defect", "inspection", "candidate")):
        return "helpful" if contract.photography_mode == "meaningful_business_object" else "unnecessary"
    return "unnecessary"


def _rectangle_dependency_score(contract) -> float:
    object_text = contract.quality_retention.business_object.lower()
    meaningful_rectangle = any(word in object_text for word in ("document", "record", "sheet", "site", "image", "profile"))
    score = 0.18 if meaningful_rectangle else 0.32
    if contract.composition_type in {"three_column", "four_stage", "dashboard", "comparison"}:
        score += 0.18
    if "panel layout" in contract.composition_family:
        score += 0.16
    if contract.dark_mass_usage != "avoid_as_default_anchor":
        score += 0.06
    return round(min(1.0, score), 3)


def _card_dependency_score(contract) -> float:
    score = 0.12
    if contract.composition_type in {"three_column", "dashboard"}:
        score += 0.32
    if contract.diagram_decision.selected_diagram in {"comparison_matrix", "kpi_dashboard", "progress_meter"}:
        score += 0.18
    if contract.quality_retention.editorial_temperature in {"high-impact editorial hero", "memorable proposition", "commitment"}:
        score -= 0.08
    return round(min(1.0, max(0.0, score)), 3)


def _visual_specificity_score(contract, rectangle_dependency: float, card_dependency: float) -> float:
    score = 0.58
    if contract.quality_retention.business_object not in {"customer business object", "customer business context"}:
        score += 0.16
    if len(_visual_representation_candidates(contract)) >= 3:
        score += 0.08
    if contract.photography_mode == "meaningful_business_object":
        score += 0.08
    if contract.typography_mode == "typography_as_visual_anchor":
        score += 0.06
    score -= rectangle_dependency * 0.18
    score -= card_dependency * 0.22
    if _is_generic_escape(contract):
        score -= 0.24
    return round(min(1.0, max(0.0, score)), 3)


def _visual_metaphor(contract) -> str:
    source_item = contract.source_basis[0] if contract.source_basis else ""
    if source_item == "background":
        return "business object as the opening world, not a decorative side diagram"
    if source_item in {"problem", "root_cause"}:
        return "visible break in the business object's continuity"
    if source_item in {"kpi", "execution_method"}:
        return "evidence object that keeps the next decision inspectable"
    if source_item in {"decision", "next_action"}:
        return "decision surface that makes the next action unavoidable"
    if contract.diagram_decision.diagram_required:
        return f"{contract.diagram_decision.selected_diagram} used as business meaning"
    return "typography and business object as the visual metaphor"


def _visual_subject(contract) -> str:
    object_text = contract.quality_retention.business_object
    if object_text not in {"customer business object", "customer business context"}:
        return object_text
    return contract.dominant_visual


def _visual_tension(contract) -> str:
    source_item = contract.source_basis[0] if contract.source_basis else ""
    if source_item in {"problem", "root_cause"}:
        return "what exists versus what cannot be reused for the next decision"
    if source_item in {"proposal_content", "risk"}:
        return "support boundary versus human accountability"
    if source_item in {"kpi", "roi", "decision", "next_action"}:
        return "evidence condition versus decision readiness"
    return "customer business object versus the decision it must unlock"


def _visual_hierarchy_path(contract) -> tuple[str, ...]:
    subject = _visual_subject(contract)
    return (
        contract.action_title,
        subject,
        contract.quality_retention.decision_role,
    )


def _visual_entry_point(contract) -> str:
    if contract.typography_mode == "typography_as_visual_anchor":
        return "hero typography"
    if contract.photography_mode == "meaningful_business_object":
        return "business-object image or crop"
    return contract.dominant_visual


def _visual_exit_point(contract) -> str:
    source_item = contract.source_basis[0] if contract.source_basis else ""
    if source_item in {"decision", "next_action", "execution_method"}:
        return "next agreement or start condition"
    if source_item in {"kpi", "roi", "risk"}:
        return "decision condition"
    return "business implication"


def _human_attention_path(contract) -> tuple[str, ...]:
    return (
        _visual_entry_point(contract),
        _visual_subject(contract),
        _visual_tension(contract),
        _visual_exit_point(contract),
    )


def _three_second_comprehension(contract, source_item: str) -> str:
    if source_item == "background":
        return "what proposal this is and what business object it changes"
    if source_item in {"problem", "root_cause"}:
        return "what is broken and why the next decision is blocked"
    if source_item in {"kpi", "execution_method", "proposal_content"}:
        return "what record, object, or boundary must be created"
    if source_item in {"decision", "next_action", "roi", "risk"}:
        return "what condition must be decided before moving forward"
    return "why this information changes the customer decision"


def _three_second_gate(contract, source_item: str) -> bool:
    specificity = _visual_specificity_score(
        contract,
        _rectangle_dependency_score(contract),
        _card_dependency_score(contract),
    )
    if specificity < 0.70:
        return False
    if _is_generic_escape(contract):
        return False
    if source_item == "background":
        return contract.typography_mode == "typography_as_visual_anchor" or contract.photography_mode == "meaningful_business_object"
    if source_item in {"problem", "root_cause"}:
        return contract.quality_retention.editorial_temperature in {"specific tension", "fracture / loss"}
    return True


def _background_temperature(contract) -> str:
    if contract.photography_mode != "none":
        return "photographic"
    if contract.dark_mass_usage != "avoid_as_default_anchor":
        return contract.dark_mass_usage
    if contract.quality_retention.editorial_temperature in {"fracture / loss", "judgment pressure"}:
        return "tension"
    return "light_editorial"


def _repeats_three(values: list[str]) -> bool:
    return any(values[index] == values[index - 1] == values[index - 2] for index in range(2, len(values)))
