# Theme Engine

Theme Engine selects the visual language for the proposal deck.

---

## Themes

| Theme | Best For | Visual Tone |
|---|---|---|
| Corporate | General BtoB proposals | Stable, clear, safe |
| Consulting | Strategy and transformation | Structured, analytical |
| Executive | CEO and board decisions | Minimal, high contrast |
| Modern | SaaS and technology | Light, spacious, crisp |
| Minimal | Short executive summaries | Sparse, focused |
| Agency | Creative, Web, brand proposals | Visual, energetic |
| Startup | New business, innovation | Bold, fast, optimistic |
| Investor | Funding, growth, ROI | Financial, metric-heavy |

---

## Inputs

- Audience
- Proposal position
- Industry
- Story type
- Decision maker
- Risk level
- Presentation length
- Brand constraints

---

## Outputs

- Color palette
- Typography scale
- Shape style
- Diagram style
- Card style
- Table style
- Accent rule
- White space level

---

## Selection Rules

| Condition | Theme |
|---|---|
| CEO / executive audience | Executive or Consulting |
| ROI and financial decision | Investor or Executive |
| Web / brand / creative proposal | Agency |
| SaaS / AI / DX proposal | Modern or Consulting |
| Internal operation improvement | Corporate or Consulting |
| High risk or regulated industry | Corporate or Executive |

---

## Theme Token Example

```json
{
  "theme_id": "executive_consulting",
  "palette": {
    "background": "#FFFFFF",
    "text": "#0B1F3A",
    "primary": "#155EEF",
    "accent": "#06AED4",
    "muted": "#667085"
  },
  "typography": {
    "headline": 34,
    "body": 18,
    "number": 44,
    "note": 11
  },
  "shape": {
    "radius": 6,
    "line_width": 1,
    "shadow": "subtle"
  }
}
```

