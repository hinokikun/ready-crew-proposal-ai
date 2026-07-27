"""Prompt boundary for the offline Evidence Planner.

Phase 2B does not call an LLM. This prompt contract documents the future
AI-backed boundary while the current implementation uses deterministic rules.
"""

EVIDENCE_PLANNER_SYSTEM_PROMPT = """
You are the Evidence Planner for Presentation Engine 2.0.
Given a Deck Blueprint and Proposal Context, create evidence requirements for
each planned slide.

You may decide:
- required evidence
- optional evidence
- evidence priority
- evidence confidence
- evidence source type
- numeric evidence requirement
- customer proof requirement
- case study requirement
- visual evidence recommendation
- missing evidence warning
- risk if missing

You must not create:
- headline
- main message
- body text
- Slide Blueprint
- layout
- diagram
- theme
- typography
- PowerPoint output
""".strip()


EVIDENCE_PLANNER_DEVELOPER_PROMPT = """
Return JSON that can be parsed as EvidencePlannerResult.
Do not invent facts. If evidence is missing, mark the confidence as missing or
unknown and add a missing evidence warning.
""".strip()


EVIDENCE_PLANNER_OUTPUT_KEYS = [
    "deck_id",
    "slide_evidence",
    "required_evidence",
    "optional_evidence",
    "evidence_priority",
    "evidence_confidence",
    "evidence_source_types",
    "numeric_evidence_required",
    "customer_proof_required",
    "case_study_required",
    "visual_evidence_recommendation",
    "missing_evidence_warnings",
    "risk_if_missing",
]


def evidence_planner_prompt_contract() -> dict[str, object]:
    return {
        "phase": "2B",
        "llm_enabled": False,
        "system_prompt": EVIDENCE_PLANNER_SYSTEM_PROMPT,
        "developer_prompt": EVIDENCE_PLANNER_DEVELOPER_PROMPT,
        "output_keys": EVIDENCE_PLANNER_OUTPUT_KEYS,
    }

