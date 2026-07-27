# Responsibility Matrix

## What Each Module Decides

| Module | Decides |
|---|---|
| Proposal Context | project facts, customer situation, known constraints |
| Deck Planner | deck goal, audience, decision stage, story arc, sections, slide order, slide role |
| Evidence Planner | required evidence, optional evidence, evidence priority, missing evidence risk |
| Message Designer | headline, main message, support points, key takeaway, evidence disclosure |
| Slide Intent | slide intent, slide type, information priority, reading order, visual pattern candidate |
| Visual Director | future visual type, visual composition, diagram choice, chart choice, visual hierarchy |
| Blueprint Composer | future renderer-ready blueprint and object structure |
| Renderer | future PowerPoint drawing operations |

## What Each Module Must Not Decide

| Module | Must Not Decide |
|---|---|
| Deck Planner | evidence details, message copy, layout, diagram, chart, PowerPoint |
| Evidence Planner | headline, body text, slide layout, visual design |
| Message Designer | coordinates, fonts, colors, theme, diagrams, charts, Slide Blueprint |
| Slide Intent | exact layout, coordinates, fonts, colors, final diagram, final chart, PPTX |
| Visual Director | business strategy, evidence truth, message copy |
| Blueprint Composer | sales strategy, claims, evidence interpretation |
| Renderer | any business meaning or content |

## Review Principle

Every downstream module may narrow or structure the prior output, but must not silently change its meaning.

If a downstream module finds a contradiction, it should emit a validation issue instead of inventing a correction.
