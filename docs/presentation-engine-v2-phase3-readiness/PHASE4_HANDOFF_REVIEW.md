# Phase4 Handoff Review

## Handoff Goal

Visual Plan Contract should be usable by the future Blueprint Composer without
requiring it to re-decide strategy or message.

## Currently Available for Phase4

- component candidates
- component priority
- source field
- evidence references
- visual strategy
- layout strategy
- emphasis strategy
- reading path
- diagram/chart/image/table/callout/icon strategies
- risk flags
- confidence

## Potentially Missing for Phase4

| Item | Status | Owner Recommendation |
|---|---|---|
| Component hierarchy | Partial | Visual Director should express candidate priority; Blueprint Composer can derive tree. |
| Component count range | Partial | Add Phase3 scoring/evaluator. |
| Preferred composition | Missing | Add as versioned extension if composer needs it. |
| Forbidden composition | Missing | Keep as risk flag initially. |
| Density target | Partial | Derive from Slide Intent density, add explicit handoff later. |
| Alignment intent | Missing | Blueprint Composer may own this. |
| Grouping intent | Partial | Component candidates imply grouping. |
| Whitespace intent | Missing | Blueprint Composer should own exact whitespace. |
| Primary focal point | Present | `visual_priority.primary_element`. |
| Secondary focal point | Present | `visual_priority.secondary_elements`. |
| Data visualization intent | Present | Chart and table strategies. |
| Image crop intent | Missing | Out of Phase3 unless image layout becomes central. |
| Table complexity | Partial | Add validator/evaluator in Phase3. |
| Fallback visual | Missing | Add in Visual Director implementation. |
| Renderer constraints | Partial | Boundary flags exist, but renderer capabilities are not modeled. |

## Phase4 Readiness

Phase4 is not blocked, but it should not start until Phase3 produces real Visual
Plan golden outputs. The main handoff gap is preferred composition detail.
