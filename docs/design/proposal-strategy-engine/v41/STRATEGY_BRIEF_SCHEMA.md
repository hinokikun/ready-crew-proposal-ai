# Strategy Brief Schema

Status: specification aligned with offline models.

## Input Model

`ProposalStrategyInput` accepts project information without requiring every field.

Main fields:

- `project_title`
- `project_summary`
- `industry`
- `business_goals`
- `current_problems`
- `proposed_solution`
- `expected_deliverables`
- `integrations`
- `schedule`
- `budget`
- `budget_type`
- `expected_kpis`
- `risks`
- `stakeholders`
- `audience_hint`
- `evidence`
- `constraints`
- `source_text`

Empty text, empty lists, and missing fields are handled safely.

## Budget Type

- `confirmed`
- `upper_limit`
- `reference`
- `unknown`

Upper-limit budget must not be treated as a formal estimate.

## Output Model

`StrategyBrief` includes:

- `schema_version`
- `project_category`
- `secondary_category`
- `primary_persona`
- `secondary_personas`
- `decision_maker`
- `primary_strategy`
- `secondary_strategies`
- `story_type`
- `primary_pack`
- `secondary_pack`
- `confidence`
- `selection_reasons`
- `assumptions`
- `missing_information`
- `evidence_summary`
- `hero_theme`
- `main_message`
- `problem_theme`
- `before_after_type`
- `architecture_type`
- `roadmap_type`
- `kpi_pack`
- `estimate_pack`
- `priority_messages`
- `risk_messages`
- `next_actions`
- `required_slide_types`
- `optional_slide_types`
- `allowed_terms`
- `conditional_terms`
- `prohibited_terms`
- `human_review_required`
- `human_review_reasons`

## Presentation Boundary

Presentation Engine should consume the Strategy Brief and should not re-decide category, strategy, or persona.
