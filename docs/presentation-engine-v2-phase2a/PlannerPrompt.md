# Planner Prompt

Phase 2A does not call an LLM. The prompt contract is documented for future AI-backed execution.

## System Boundary

The planner may decide:

- Deck Goal
- Audience
- Decision Stage
- Story Arc
- Deck Length
- Section sequence
- Slide order
- Slide role and purpose
- Recommended visual category
- Recommended evidence level
- CTA placement
- Executive Summary, ROI, Pricing, Appendix presence

The planner must not decide:

- Final headline
- Body text
- Diagram definition
- Color
- Coordinates
- Font
- Shape
- PowerPoint rendering

## Output

The output must be convertible into `DeckPlannerResult` and must include a valid `DeckBlueprint`.

