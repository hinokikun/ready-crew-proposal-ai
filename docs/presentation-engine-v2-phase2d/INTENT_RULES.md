# Intent Rules

## Primary Mapping

| Section | Intent | Visual Pattern |
|---|---|---|
| cover | frame_decision | hero |
| executive_summary | summarize | summary_cards |
| problem | explain_problem | callout |
| current_state | explain_problem | process |
| competitor | compare_options | comparison |
| strategy | recommend_action | summary_cards |
| solution | recommend_action | process |
| roadmap | show_plan | roadmap |
| timeline | show_plan | timeline |
| kpi | prove_value | kpi_cards |
| roi | explain_investment | number_dominant |
| pricing / estimate | explain_investment | table |
| risk / faq | reduce_risk | matrix / checklist |
| next_action / closing | close_next_step | checklist / callout |

## Evidence-aware Rules

- Chart candidates are emitted only when numeric claims exist and missing evidence is not present.
- Missing evidence adds `SHOW_EVIDENCE_GAP`.
- High information density adds `SPLIT_IF_DENSE`.
- ROI, KPI, pricing, and estimate add `REQUIRE_NUMERIC_EVIDENCE` and `AVOID_FAKE_NUMBERS`.

## Runtime Boundary

Every output keeps the following false:

- `generated_slide_blueprint`
- `generated_diagram`
- `generated_chart`
- `generated_pptx`
- `connected_to_runtime`
