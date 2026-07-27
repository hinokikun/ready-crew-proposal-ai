# Hierarchy Engine

Hierarchy Engine designs how the audience reads the slide.

---

## Responsibilities

- Decide primary, secondary, and tertiary information.
- Define gaze path.
- Set font sizes and visual weight.
- Place key evidence near the claim.
- Allocate white space.
- Reduce cognitive load.

---

## Hierarchy Levels

| Level | Role | Typical Treatment |
|---|---|---|
| Level 1 | Main message | Headline or dominant metric |
| Level 2 | Supporting evidence | Cards, table rows, callouts |
| Level 3 | Detail | Notes, assumptions, source labels |
| Level 4 | Navigation | Page number, section marker |

---

## Gaze Path

Every slide must define a gaze path:

```json
{
  "gaze_path": [
    "headline",
    "primary_metric",
    "comparison_axis",
    "cta"
  ]
}
```

---

## Layout Zones

| Zone | Use |
|---|---|
| Top band | Takeaway headline |
| Left anchor | Context or current state |
| Center stage | Main diagram or metric |
| Right proof | Evidence, risk, or implication |
| Bottom action | CTA, assumptions, next step |

---

## Rules

- The most important item must be visually dominant.
- Notes must never compete with the headline.
- Same-level elements must align.
- If a slide has no clear Level 1 element, it must be redesigned.

