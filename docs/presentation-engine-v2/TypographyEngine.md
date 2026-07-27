# Typography Engine

Typography Engine defines the type hierarchy for each slide.

---

## Type Roles

| Role | Purpose | Default Size |
|---|---|---:|
| Deck title | Cover title | 44-54 pt |
| Slide headline | Takeaway title | 30-38 pt |
| Section label | Navigation | 9-12 pt |
| Body | Main explanation | 16-20 pt |
| Card title | Small group label | 18-24 pt |
| Metric number | Key numerical value | 38-52 pt |
| Metric label | Metric description | 12-16 pt |
| Note | Assumption or source | 10-12 pt |

---

## Rules

- Body text should normally be 16 pt or larger.
- Notes may be 10 pt or larger.
- Slide headlines should normally be 30 pt or larger.
- Do not shrink text to solve overcrowding.
- If body text needs to go below 16 pt, use White Space Optimizer.
- Numbers must be visually larger than their explanatory labels.

---

## Japanese Typography Notes

- Prefer readable Japanese sans-serif fonts.
- Avoid mixing many Japanese font families.
- Use slightly larger line height for Japanese body copy.
- Avoid dense long-line paragraphs.
- Use short phrases instead of full sentences inside diagrams.

---

## Output Example

```json
{
  "headline": {"size_pt": 34, "weight": "bold"},
  "body": {"size_pt": 18, "weight": "regular"},
  "number": {"size_pt": 46, "weight": "bold"},
  "note": {"size_pt": 11, "weight": "regular"}
}
```

