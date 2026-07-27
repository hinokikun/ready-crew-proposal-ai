# White Space Optimizer

White Space Optimizer prevents dense slides and improves readability.

---

## Responsibilities

- Detect overcrowding.
- Compress copy safely.
- Split slides when needed.
- Convert dense text into cards or diagrams.
- Balance canvas margins.
- Prevent excessive empty space.

---

## Density Signals

| Signal | Action |
|---|---|
| More than 5 bullets | Compress or split |
| More than 250 Japanese characters | Compress or split |
| More than 3 concepts | Split by concept |
| Table with more than 5 columns | Reduce columns or split |
| Body font below 16 pt | Split or diagram |
| Many equal-weight cards | Group or prioritize |

---

## Actions

| Action | Meaning |
|---|---|
| Compress | Shorten text without changing meaning |
| Split | Create additional slide |
| Diagramize | Convert text into editable diagram |
| Promote | Move a key item into headline or callout |
| Demote | Move detail to note or appendix |
| Remove | Cut non-essential content |

---

## Output Example

```json
{
  "density": "high",
  "recommended_action": "split",
  "reason": "The slide contains process, KPI, and risk content at the same level.",
  "split_plan": [
    {"slide_goal": "process overview"},
    {"slide_goal": "measurement criteria"}
  ]
}
```

