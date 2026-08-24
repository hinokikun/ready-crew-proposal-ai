from __future__ import annotations

from typing import Any


PHASE4C_GRAMMAR_CONTRACT: dict[str, Any] = {
    "source_of_truth": "phase4c_human_approved_visual_grammar",
    "visual_logic_duplication_policy": "production module is the single runtime contract; artifact scripts are reference only",
    "runtime_artifact_dependency": False,
    "quality_axes": [
        "Input Understanding",
        "Story / Narrative",
        "Art Direction",
        "Business Reality Contract",
        "Meaning-to-Visual",
        "Visual Representation Selection",
        "Business Object",
        "Structural Fingerprint",
        "Anti-template divergence",
        "Photography Decision",
        "Composition selection",
        "Typography variation",
        "Density rhythm",
        "Evidence representation",
        "Decision representation",
        "Next Action representation",
        "Fake Data Guard",
        "Overflow Guard",
    ],
    "business_reality_contract": {
        "required": [
            "real_actor",
            "real_work_object",
            "real_action",
            "real_handoff",
            "real_decision",
            "real_context",
        ],
        "avoid": [
            "generic card grids",
            "generic dashboard UI",
            "same-role visual skeleton reuse",
            "decorative photography without business meaning",
            "invented KPI/ROI/accuracy/sample counts",
        ],
    },
    "qa_boundary": {
        "runtime_blocking": [
            "broken_pptx",
            "generation_exception",
            "critical_fake_data_violation",
            "critical_placeholder_leakage",
        ],
        "runtime_warning": [
            "unknown_category",
            "missing_optional_business_detail",
            "low_business_specificity_signal",
        ],
        "offline_only": [
            "cross_case_similarity",
            "role_level_structural_similarity",
            "engine_signature_score",
            "reference_visual_similarity",
        ],
    },
    "approved_role_fingerprints": {
        "Cover": ["spatial", "center-left-building", "left-arc"],
        "Problem": ["horizontal-gap", "vertical-and-random", "radial"],
        "Business Object": ["curved-trail", "property-grid", "bridge"],
        "Evidence": ["lens-trail", "scatter-response", "orbit-plus-sheet"],
        "Decision": ["circle-gate", "grid-plus-heat", "boundary"],
        "Next Action": ["map-badge", "matrix-to-dark-team", "boundary-close"],
    },
}


def grammar_contract_summary() -> dict[str, Any]:
    return {
        "source_of_truth": PHASE4C_GRAMMAR_CONTRACT["source_of_truth"],
        "visual_logic_duplication": 0,
        "artifact_runtime_dependency": False,
        "quality_axes": PHASE4C_GRAMMAR_CONTRACT["quality_axes"],
        "qa_boundary": PHASE4C_GRAMMAR_CONTRACT["qa_boundary"],
    }


def golden_regression_cases() -> tuple[dict[str, str], ...]:
    return (
        {
            "case_id": "case_11",
            "source_phase": "phase4c",
            "customer": "Seaside Tourism Board",
            "domain": "Tourism Marketing",
            "art_direction": "immersive destination field",
        },
        {
            "case_id": "case_14",
            "source_phase": "phase4c",
            "customer": "Prime Estate",
            "domain": "Real Estate Sales",
            "art_direction": "commercial property decision field",
        },
        {
            "case_id": "case_19",
            "source_phase": "phase4c",
            "customer": "Orbit Systems",
            "domain": "Onboarding Productivity",
            "art_direction": "human readiness boundary",
        },
        {
            "case_id": "case_17",
            "source_phase": "phase3",
            "customer": "Commerce / Customer Journey",
            "domain": "Creative / Web / Marketing",
            "art_direction": "commerce journey",
        },
        {
            "case_id": "case_05",
            "source_phase": "phase3",
            "customer": "Industrial Evidence",
            "domain": "Industrial / QA",
            "art_direction": "industrial evidence",
        },
        {
            "case_id": "case_10",
            "source_phase": "phase3",
            "customer": "Human Judgment",
            "domain": "Human Judgment / Operations",
            "art_direction": "human judgment",
        },
    )
