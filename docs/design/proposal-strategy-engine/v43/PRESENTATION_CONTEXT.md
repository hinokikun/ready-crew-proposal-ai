# Presentation Context

Status: implemented as `PresentationContext` model.

## Purpose

Presentation Context is the rendering contract for future Presentation Engine integration.

It contains information needed for slide generation without requiring Presentation Engine to re-decide strategy.

## Fields

| Field | Meaning |
|---|---|
| `schema_version` | Presentation Context schema version. |
| `source_strategy_schema_version` | Source Strategy Brief schema version. |
| `review_status` | Approved review status. |
| `hero` | Hero theme, message, and persona. |
| `main_message` | Main proposal message. |
| `problem_theme` | Problem framing. |
| `architecture_type` | Architecture visualization type. |
| `roadmap_type` | Roadmap structure. |
| `kpi_pack` | KPI visualization pack. |
| `estimate_pack` | Estimate structure pack. |
| `slide_order` | Required and optional slides in order. |
| `visual_theme` | Presentation visual theme identifier. |
| `presentation_pack` | Primary presentation pack. |
| `secondary_presentation_pack` | Secondary pack if needed. |
| `required_slides` | Required slide types. |
| `optional_slides` | Optional slide types. |
| `priority_messages` | Messages to emphasize. |
| `risk_messages` | Risk framing messages. |
| `next_actions` | Next action messages. |
| `allowed_terms` | Terms allowed by selected pack. |
| `conditional_terms` | Terms allowed when secondary pack is used. |
| `prohibited_terms` | Terms future rendering should not inject. |

## Excluded Fields

Presentation Context intentionally excludes:

- `confidence`
- `selection_reasons`
- `evidence_summary`
- `human_review_reasons`

These belong to Strategy Review, not slide rendering.
