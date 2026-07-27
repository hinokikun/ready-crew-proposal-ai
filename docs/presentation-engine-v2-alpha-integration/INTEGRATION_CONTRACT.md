# Integration Contract

## Input

`AlphaIntegrationCase` contains:

- integration_case_id
- case_name
- proposal_context
- expected_deck_characteristics
- expected_evidence_characteristics
- expected_message_characteristics
- review_tags
- industry
- proposal_category
- audience
- decision_stage
- deck_length_preference
- known_constraints
- available_evidence
- intentionally_missing_evidence
- schema_version

## Output

`AlphaIntegrationOutput` contains:

- deck_planner_result
- deck_validation_result
- evidence_planner_result
- evidence_validation_result
- message_designer_result
- message_validation_result
- cross_module_validation_result
- pipeline_evaluation_result
- human_review_summary
- blocking_issues
- warnings
- improvement_candidates
- phase2d_readiness
- input_fingerprint

