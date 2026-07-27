# Slide Intent AI

Slide Intent AI determines the job of each slide.

---

## Intent Types

| Intent | Purpose |
|---|---|
| Problem Sharing | Align on the issue |
| Current State | Explain the present workflow or situation |
| Comparison | Show options, before/after, or competitor differences |
| ROI | Explain financial or time impact |
| Roadmap | Show staged adoption |
| Timeline | Show schedule and milestones |
| CTA | Ask for decision or next action |
| Case Study | Provide proof |
| Price Explanation | Explain cost, scope, and assumptions |
| Risk Handling | Address concerns |
| Architecture | Explain system or operating model |
| KPI | Define success metrics |

---

## Inputs

- Story outline
- Slide draft text
- Audience
- Strategy type
- Evidence
- Required slide count

---

## Outputs

```json
{
  "slide_id": "slide-03",
  "intent": "Comparison",
  "reason": "The content contrasts current manual proposal creation with AI-supported workflow.",
  "audience_need": "Understand what changes and what stays human-controlled.",
  "success_criteria": "Reader can explain the Before / After in 10 seconds."
}
```

---

## Rules

- One slide should have one primary intent.
- If two intents compete, split the slide.
- Intent must be audience-facing, not renderer-facing.
- Intent must be decided before layout.

---

## Version81 Gap

Version81 classified slide type mostly from text keywords. Presentation Engine 2.0 must classify why the slide exists, not only what words it contains.

