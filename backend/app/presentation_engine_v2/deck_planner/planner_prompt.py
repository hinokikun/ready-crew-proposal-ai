"""Prompt contract for the offline Deck Planner.

Phase 2A does not call an LLM. This module documents the prompt boundary that
future AI-backed planners must obey while the current planner uses deterministic
rules.
"""

DECK_PLANNER_SYSTEM_PROMPT = """
You are the Deck Planner for Presentation Engine 2.0.
Your task is to produce a Deck Blueprint plan from Proposal Context.
You must decide only deck-level strategy and structure:
- deck goal
- audience
- decision stage
- story arc
- deck length
- section sequence
- slide order
- each slide role and purpose
- recommended visual category
- recommended evidence level
- CTA placement
- whether executive summary, ROI, pricing, and appendix are needed

You must not produce final headlines, body copy, diagrams, colors, coordinates,
fonts, PowerPoint shapes, or rendered slides.
""".strip()


DECK_PLANNER_DEVELOPER_PROMPT = """
Return a JSON object that can be converted into DeckPlannerResult.
Keep all facts grounded in Proposal Context.
If a field is unknown, plan a review point instead of inventing a fact.
Use the Presentation Engine 2.0 Deck Blueprint schema version
pe2_deck_blueprint_v1.
""".strip()


DECK_PLANNER_OUTPUT_KEYS = [
    "deck_goal",
    "audience",
    "decision_stage",
    "story_arc",
    "deck_length",
    "sections",
    "slide_plan",
    "slide_recommendations",
    "cta_plan",
    "decisions",
    "warnings",
]


def planner_prompt_contract() -> dict[str, object]:
    return {
        "system_prompt": DECK_PLANNER_SYSTEM_PROMPT,
        "developer_prompt": DECK_PLANNER_DEVELOPER_PROMPT,
        "output_keys": DECK_PLANNER_OUTPUT_KEYS,
        "llm_enabled": False,
        "phase": "2A",
    }

