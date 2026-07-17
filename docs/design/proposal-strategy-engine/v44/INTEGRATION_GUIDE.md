# Integration Guide

## Integration Layer

Version 44 adds `presentation_engine_integration.py`.

Its responsibility is limited to:

```text
Engine Mode
-> optional approved Review Report
-> Presentation Context
-> existing PPTX generation
```

It does not perform strategy selection itself.

## Legacy Path

When mode is `legacy`:

- Strategy Engine is not called.
- Strategy Adapter is not called.
- Presentation Context is not created.
- Existing PPTX payload is passed to the legacy generator.

## Strategy Path

When mode is `strategy_v1`:

- `strategy_review_report` must be present in the PPTX request.
- The report status must be `approved` or `approved_with_changes`.
- The adapter converts it to `PresentationContext`.
- The existing PPTX generator receives the original payload plus `PresentationContext`.

## Existing Generator Compatibility

The current PPTX generator uses `proposal_category` internally.

In strategy mode, the generator derives that category from `presentation_pack` instead of re-running the legacy text-based category decision.

Current mapping:

| Presentation Pack | Legacy PPTX Category |
|---|---|
| `vision_ocr` | `ai_ocr` |
| `automation` | `rpa` |
| `conversational_ai` | `ai_agent` |
| `knowledge_ai` | `generative_ai` |
| `crm_sales_intelligence` | `crm_sfa` |
| `generative_ai_transformation` | `generative_ai` |
| `digital_experience` | `web` |
| `generic_consulting` | `other` |

## Boundary Rule

Presentation Engine must not re-decide:

- Strategy
- Persona
- Story
- Presentation Pack

Those decisions belong upstream to the approved Strategy Brief workflow.
