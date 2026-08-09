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
                "priority": contract.information_priority,
                "reading_order": contract.reading_order,
                "focal_point": contract.focal_point,
                "secondary_point": contract.secondary_point,
            }
            for contract in deck.slide_contracts
        ],
        "repeated_composition": has_repeated_composition(deck),
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
