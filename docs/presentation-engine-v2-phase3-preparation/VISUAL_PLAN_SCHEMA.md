# Visual Plan Schema

## Schema Helpers

The schema is available through:

- `input_schema()`
- `output_schema()`
- `visual_plan_item_schema()`
- `example_visual_plan_contract()`
- `invalid_visual_plan_examples()`
- `schema_json()`

## Input Schema

`VisualDirectorInput` references existing upstream contracts:

- `ProposalContext`
- `DeckBlueprint`
- `EvidencePlannerResult`
- `MessageDesignerOutput`
- `SlideIntentOutput`

## Output Schema

`VisualPlanContract` is renderer-agnostic and contains deck-level defaults plus
one `VisualPlanItem` per slide.

## Example

The example uses a callout-style Visual Plan with:

- `message_first`
- `callout_focus`
- `main_message`
- component candidates for headline and evidence callout

## Invalid Examples

Invalid examples cover:

- missing `visual_strategy`
- chart selected without numeric evidence
- downstream generation boundary violation

## Version

Current contract version:

`pe2_visual_plan_contract_v1`
