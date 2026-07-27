# Message Contract Decisions

## Contract Unit

The smallest contract unit is `SlideMessageDesign`.

## Identity

Each message has:

- `message_design_id`
- `deck_id`
- `slide_plan_id`
- `slide_blueprint_id`
- `slide_order`
- `input_fingerprint`

IDs are deterministic so offline tests can compare outputs.

## Evidence Safety

Evidence Planner IDs are preserved in:

- `used_evidence_ids`
- `unused_required_evidence_ids`
- `evidence_usage`
- `missing_evidence_disclosure`
- `source_references`

Unsupported numeric or ROI claims are not created. If evidence is missing, the message is weakened and disclosure is added.

