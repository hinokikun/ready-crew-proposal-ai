# Contract

## Input

`SalesAssistantInput` contains:

- `strategy_brief`
- `project_title`
- `project_summary`
- `client_name`
- `known_requirements`
- `known_constraints`
- `budget_information`
- `schedule_information`
- `meeting_stage`
- `previous_interactions`
- `evidence_items`

## Output

`SalesAssistantBrief` contains exactly these top-level sections:

1. `summary`
2. `meeting_plan`
3. `discovery_questions`
4. `talk_track`
5. `objection_handling`
6. `decision_maker_support`
7. `evidence_guidance`
8. `next_actions`
9. `follow_up`
10. `risk_and_guardrails`
11. `generation_metadata`

## Minimum fields

`summary`

- `sales_objective`
- `recommended_positioning`
- `primary_message`
- `confidence`
- `human_review_required`
- `human_review_reasons`

`meeting_plan`

- `meeting_stage`
- `recommended_duration_minutes`
- `opening`
- `agenda`
- `desired_outcome`
- `next_step_goal`

`discovery_questions`

- `question`
- `purpose`
- `priority`
- `target_persona`
- `required`
- `follow_up_questions`

`talk_track`

- `opening_talk`
- `problem_confirmation`
- `proposal_explanation`
- `value_explanation`
- `differentiation_talk`
- `budget_talk`
- `schedule_talk`
- `closing_talk`

`objection_handling`

- `objection_type`
- `expected_objection`
- `recommended_response`
- `supporting_evidence`
- `prohibited_claims`
- `escalation_required`

`decision_maker_support`

- `likely_decision_criteria`
- `approval_barriers`
- `information_required_for_approval`
- `recommended_materials`
- `internal_explanation_points`

`evidence_guidance`

- `usable_evidence`
- `conditional_evidence`
- `missing_evidence`
- `claims_requiring_review`

`next_actions`

- `action`
- `owner`
- `priority`
- `timing`
- `completion_condition`

`follow_up`

- `email_subject`
- `email_body`
- `meeting_summary_template`
- `requested_client_actions`
- `internal_follow_up_actions`

`risk_and_guardrails`

- `allowed_terms`
- `conditional_terms`
- `prohibited_terms`
- `unsupported_claims`
- `compliance_notes`

`generation_metadata`

- `generator_version`
- `strategy_brief_version`
- `selected_rules`
- `warnings`
- `fallback_reasons`

All models are Pydantic models and are JSON serializable.
