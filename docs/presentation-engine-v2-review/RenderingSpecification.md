# Rendering Specification

The PowerPoint Renderer is a deterministic drawing layer. It must render the blueprint into editable PowerPoint objects without making AI decisions.

---

## 1. Renderer Principles

The renderer must:

- draw only what exists in the validated blueprint
- preserve source text and numbers
- create editable PowerPoint shapes whenever possible
- use theme tokens and typography tokens from the blueprint
- report structured validation errors
- never call an LLM
- never infer strategy, message, visual type, or slide intent

The renderer must not:

- rewrite copy
- shorten text by itself
- invent values
- choose diagrams
- choose themes
- silently hide overflowing content without warning
- rasterize text into images

---

## 2. Canvas

| Item | Rule |
|---|---|
| Aspect ratio | 16:9 by default |
| Slide size | 13.333 x 7.5 inches or equivalent |
| Coordinate system | normalized 0.0 to 1.0 or absolute inches, but not mixed within one blueprint |
| Safe area | default 5 percent from each edge |
| Bleed | not used unless print deck is explicitly requested |
| Background | theme background color or blueprint-defined shape |

---

## 3. Grid

| Grid element | Rule |
|---|---|
| Columns | 12-column logical grid |
| Rows | 8-row logical grid |
| Gutter | theme-defined, default 0.18 inches |
| Outer margin | theme-defined, minimum 0.35 inches |
| Alignment | all primary elements align to grid unless intentionally full bleed |
| Snap | renderer snaps element bounds to grid within tolerance |

Example:

```json
{
  "grid": {
    "columns": 12,
    "rows": 8,
    "margin": {"top": 0.42, "right": 0.48, "bottom": 0.42, "left": 0.48},
    "gutter": 0.16
  }
}
```

---

## 4. Safe Area

- Titles must stay inside the safe area.
- Page numbers and footers must stay inside the footer zone.
- Logos must not overlap the title or page number.
- Diagrams may extend near edges only when `full_bleed_allowed=true`.
- No text may be placed within 0.18 inches of the slide edge.

---

## 5. Z-order

| Layer | Content |
|---:|---|
| 0 | slide background |
| 10 | decorative background shapes |
| 20 | image placeholders |
| 30 | cards and containers |
| 40 | diagrams and charts |
| 50 | text |
| 60 | icons |
| 70 | annotations and callouts |
| 80 | header/footer/page number |

Renderer must respect explicit `z_index` values when present.

---

## 6. Titles

| Title type | Rule |
|---|---|
| Deck cover title | 42-56 pt |
| Standard slide headline | 30-40 pt |
| Section title | 36-48 pt |
| Subtitle | 18-24 pt |
| Kicker label | 10-12 pt uppercase or small label |

Title requirements:

- maximum 90 characters
- no more than 2 lines unless section divider
- clear contrast with background
- must not overlap logo or page number

---

## 7. Body Text

| Body role | Rule |
|---|---|
| Standard body | 17-20 pt |
| Dense technical body | minimum 16 pt, appendix only |
| Notes | 10-12 pt |
| Chart labels | minimum 10 pt |
| Table cells | minimum 11 pt |

Content fit rules:

- If body text cannot fit at minimum size, renderer returns `TEXT_OVERFLOW`.
- Renderer may use blueprint-provided condensed variant only if present.
- Renderer may not summarize text itself.

---

## 8. Cards

Cards must define:

- bounds
- fill
- border
- radius
- padding
- title role
- body role
- icon slot if used

Card rules:

- minimum internal padding: 0.12 inches
- card title minimum: 14 pt
- card body minimum: 12 pt for dense cards, 17 pt for main message cards
- max cards on one standard slide: 6
- max KPI cards on one slide: 5

---

## 9. Tables

| Table attribute | Rule |
|---|---|
| Maximum columns | 5 in main deck |
| Maximum rows | 8 in main deck |
| Header | required |
| Cell text | min 11 pt |
| Zebra rows | allowed when theme supports |
| Alignment | numeric right, labels left |

Renderer must reject tables that exceed limits unless slide type is appendix.

---

## 10. Icons

Icon rules:

- Use a single icon style per deck.
- Stroke width must be consistent.
- Icons must include semantic role metadata.
- Icons are decorative only when `aria_label` is empty and `decorative=true`.
- Icon size default: 20-32 px equivalent.
- Hero icons may be 48-72 px equivalent.

Renderer must not fetch external icons during rendering.

---

## 11. Diagrams

Diagram rendering requires:

- diagram type
- nodes
- connectors
- groups or lanes when applicable
- label positions
- reading order
- fallback diagram

Diagram rules:

- connectors must not cross text when avoidable
- arrow labels must be short
- node count should not exceed catalog constraints
- every diagram needs a clear starting point
- loop diagrams need direction markers

---

## 12. Images and Placeholders

Images may be:

- external licensed assets
- generated assets with provenance
- product screenshots
- placeholders for later replacement

Every image object must include:

```json
{
  "image_role": "hero_placeholder",
  "source_type": "placeholder",
  "license": "not_applicable",
  "alt_text": "Abstract product visual placeholder",
  "crop_policy": "cover",
  "replaceable": true
}
```

Renderer must not embed untracked external images without asset metadata.

---

## 13. Charts

Chart requirements:

- chart type
- data series
- axis labels
- value format
- source or assumption label
- chart style token

Renderer must not compute missing values. If a value is missing, it must render a placeholder or return a validation error.

---

## 14. Header, Footer, Page Number

| Element | Rule |
|---|---|
| Header | optional; avoid on cover |
| Footer | may include brand, confidentiality, date |
| Page number | required except cover and section dividers unless disabled |
| Logo | one location per theme |
| Confidential label | required only when blueprint specifies |

Footer text must not exceed 10-11 pt and must not compete with slide content.

---

## 15. Accessibility

Renderer should produce:

- reading order metadata
- alt text for images and diagrams
- sufficient contrast
- no text below minimum floor
- no color-only distinction for critical meaning

---

## 16. Validation Errors

| Code | Meaning |
|---|---|
| `INVALID_BLUEPRINT` | schema validation failed |
| `UNSUPPORTED_DIAGRAM` | diagram type is not supported |
| `TEXT_OVERFLOW` | text cannot fit in allowed area |
| `MISSING_THEME_TOKEN` | required theme token missing |
| `MISSING_ASSET_METADATA` | image or icon metadata missing |
| `UNSAFE_FONT_SIZE` | rendered text would be too small |
| `TABLE_TOO_DENSE` | table exceeds main-deck limit |
| `NUMERIC_INTEGRITY_RISK` | number changed or missing |

---

## 17. Renderer Acceptance Criteria

A rendered deck passes only when:

- PPTX opens without repair
- all text is editable
- no broken relationships exist
- no external references remain unless explicitly allowed
- no body text below 17 pt in main slides
- all required page numbers appear
- slide content stays inside safe area
- diagrams are editable shapes
- all warnings are written to rendering metadata
