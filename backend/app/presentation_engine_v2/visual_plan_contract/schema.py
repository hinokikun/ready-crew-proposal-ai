"""JSON Schema helpers for the Visual Plan Contract."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from .contracts import VISUAL_PLAN_SCHEMA_DRAFT
from .enums import (
    CalloutStrategy,
    ChartStrategy,
    ComponentCandidateType,
    DiagramStrategy,
    EmphasisStrategy,
    IconStrategy,
    ImageStrategy,
    LayoutStrategy,
    TableStrategy,
    VisualConfidence,
    VisualPriorityLevel,
    VisualReadingOrder,
    VisualStrategy,
)
from .models import (
    CalloutStrategyPlan,
    ChartStrategyPlan,
    ComponentCandidate,
    DiagramStrategyPlan,
    IconStrategyPlan,
    ImageStrategyPlan,
    TableStrategyPlan,
    VisualDirectorInput,
    VisualPlanContract,
    VisualPlanItem,
    VisualPriorityPlan,
)


def input_schema() -> dict[str, Any]:
    schema = VisualDirectorInput.schema()
    schema["$schema"] = VISUAL_PLAN_SCHEMA_DRAFT
    schema["$id"] = "https://proposalpilot.local/schemas/presentation-engine-v2/visual-director-input.schema.json"
    schema["title"] = "Presentation Engine 2.0 Visual Director Input"
    schema["x-phase"] = "phase3-preparation"
    schema["x-runtime-connected"] = False
    return schema


def output_schema() -> dict[str, Any]:
    schema = VisualPlanContract.schema()
    schema["$schema"] = VISUAL_PLAN_SCHEMA_DRAFT
    schema["$id"] = "https://proposalpilot.local/schemas/presentation-engine-v2/visual-plan-contract.schema.json"
    schema["title"] = "Presentation Engine 2.0 Visual Plan Contract"
    schema["x-phase"] = "phase3-preparation"
    schema["x-runtime-connected"] = False
    return schema


def visual_plan_item_schema() -> dict[str, Any]:
    schema = VisualPlanItem.schema()
    schema["$schema"] = VISUAL_PLAN_SCHEMA_DRAFT
    schema["$id"] = "https://proposalpilot.local/schemas/presentation-engine-v2/visual-plan-item.schema.json"
    schema["title"] = "Presentation Engine 2.0 Visual Plan Item"
    schema["x-phase"] = "phase3-preparation"
    return schema


def _sample_priority() -> VisualPriorityPlan:
    return VisualPriorityPlan(
        primary_element="main_message",
        secondary_elements=["supporting evidence", "next action"],
        muted_elements=["unsupported claims"],
        priority_level=VisualPriorityLevel.PRIMARY,
        rationale="The message should lead while supporting evidence remains visible.",
    )


def _sample_components() -> list[ComponentCandidate]:
    return [
        ComponentCandidate(
            component_id="component-headline",
            component_type=ComponentCandidateType.HEADLINE_BLOCK,
            priority_level=VisualPriorityLevel.PRIMARY,
            source_field="message.headline",
            purpose="Show the slide headline as the first reading anchor.",
            evidence_ids=[],
            placeholder_allowed=False,
            renderer_hint="Renderer may create an editable headline container later.",
        ),
        ComponentCandidate(
            component_id="component-evidence",
            component_type=ComponentCandidateType.EVIDENCE_CALLOUT,
            priority_level=VisualPriorityLevel.SUPPORTING,
            source_field="evidence.required_evidence",
            purpose="Keep required proof visible without writing new claims.",
            evidence_ids=["evidence-001"],
            placeholder_allowed=False,
            renderer_hint="Renderer may create an editable evidence callout later.",
        ),
    ]


def _sample_item() -> VisualPlanItem:
    return VisualPlanItem(
        visual_plan_id="visual-plan-001",
        deck_id="deck-sample",
        slide_blueprint_id="slide-001",
        source_intent_id="intent-001",
        slide_order=1,
        visual_strategy=VisualStrategy.MESSAGE_FIRST,
        layout_strategy=LayoutStrategy.CALLOUT_FOCUS,
        emphasis_strategy=EmphasisStrategy.MAIN_MESSAGE,
        visual_priority=_sample_priority(),
        reading_order=VisualReadingOrder.TITLE_FIRST,
        component_candidates=_sample_components(),
        diagram_strategy=DiagramStrategyPlan(
            strategy=DiagramStrategy.CALLOUT,
            rationale="A callout can emphasize the main point without creating a diagram.",
            required_evidence_ids=["evidence-001"],
        ),
        chart_strategy=ChartStrategyPlan(
            strategy=ChartStrategy.NONE,
            rationale="No numeric evidence is required for this sample visual plan.",
        ),
        image_strategy=ImageStrategyPlan(
            strategy=ImageStrategy.NONE,
            rationale="No image asset is required for this slide.",
        ),
        table_strategy=TableStrategyPlan(
            strategy=TableStrategy.NONE,
            rationale="A table would add unnecessary structure for one message.",
        ),
        callout_strategy=CalloutStrategyPlan(
            strategy=CalloutStrategy.KEY_TAKEAWAY,
            rationale="The slide should surface the key takeaway.",
            callout_source="message.key_takeaway",
        ),
        icon_strategy=IconStrategyPlan(
            strategy=IconStrategy.FUNCTIONAL,
            rationale="A simple functional icon may support scanability.",
            icon_concepts=["decision", "evidence"],
        ),
        risk_flags=[],
        confidence=VisualConfidence.MEDIUM,
        rationale="The plan preserves Slide Intent while staying renderer-agnostic.",
        source_visual_pattern_candidate="callout",
        source_diagram_candidate="callout",
        source_chart_candidate="none",
        source_reading_order="title_first",
        source_evidence_ids=["evidence-001"],
        numeric_evidence_ids=[],
        input_fingerprint="sample-visual-plan-fingerprint",
        created_at=datetime(2026, 1, 1),
    )


def example_visual_plan_contract() -> dict[str, Any]:
    item = _sample_item()
    contract = VisualPlanContract(
        created_at=datetime(2026, 1, 1),
        deck_id="deck-sample",
        project_id="project-sample",
        project_name="Sample proposal",
        visual_plan=[item],
        visual_strategy=VisualStrategy.MESSAGE_FIRST,
        layout_strategy=LayoutStrategy.CALLOUT_FOCUS,
        emphasis_strategy=EmphasisStrategy.MAIN_MESSAGE,
        visual_priority=_sample_priority(),
        component_candidates=_sample_components(),
        diagram_strategy=item.diagram_strategy,
        chart_strategy=item.chart_strategy,
        image_strategy=item.image_strategy,
        table_strategy=item.table_strategy,
        callout_strategy=item.callout_strategy,
        icon_strategy=item.icon_strategy,
        risk_flags=[],
        confidence=VisualConfidence.MEDIUM,
        source_contracts=[
            "proposal_context",
            "deck_blueprint",
            "evidence_planner_output",
            "message_designer_output",
            "slide_intent_output",
        ],
    )
    return contract.dict()


def invalid_visual_plan_examples() -> list[dict[str, Any]]:
    missing_strategy = example_visual_plan_contract()
    missing_strategy.pop("visual_strategy", None)

    chart_without_numeric = example_visual_plan_contract()
    chart_without_numeric["visual_plan"][0]["chart_strategy"]["strategy"] = ChartStrategy.BAR.value
    chart_without_numeric["visual_plan"][0]["chart_strategy"]["numeric_evidence_ids"] = []

    boundary_crossing = example_visual_plan_contract()
    boundary_crossing["generated_pptx"] = True
    boundary_crossing["visual_plan"][0]["generated_coordinates"] = True
    return [missing_strategy, chart_without_numeric, boundary_crossing]


def schema_json() -> str:
    return json.dumps(
        {
            "input": input_schema(),
            "output": output_schema(),
            "visual_plan_item": visual_plan_item_schema(),
            "example": example_visual_plan_contract(),
            "invalid_examples": invalid_visual_plan_examples(),
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
        default=str,
    )
