# Theme Specification

Presentation Engine 2.0 themes are token sets. A theme does not decide the message, slide intent, or diagram structure. It only provides visual language tokens for the renderer.

---

## 1. Theme Contract

```json
{
  "theme_id": "consulting",
  "display_name": "Consulting",
  "recommended_for": ["executive proposal", "strategy proposal"],
  "avoid_for": ["playful campaign deck"],
  "color_palette": {},
  "spacing": {},
  "typography": {},
  "cards": {},
  "icons": {},
  "shapes": {},
  "charts": {},
  "photos": {}
}
```

---

## 2. Shared Token Scale

| Token | Value |
|---|---|
| `space_1` | 4 px |
| `space_2` | 8 px |
| `space_3` | 12 px |
| `space_4` | 16 px |
| `space_5` | 24 px |
| `space_6` | 32 px |
| `space_7` | 48 px |
| `space_8` | 64 px |
| `radius_small` | 4 px |
| `radius_medium` | 8 px |
| `radius_large` | 16 px |
| `shadow_none` | none |
| `shadow_subtle` | 0 6 16 rgba(15,23,42,0.08) |
| `shadow_deep` | 0 18 42 rgba(15,23,42,0.18) |

---

## 3. Theme Definitions

### 3.1 Corporate

| Area | Definition |
|---|---|
| Use case | enterprise, stable operations, governance, security |
| Colors | navy `#0F172A`, blue `#2563EB`, slate `#475569`, white `#FFFFFF`, light blue `#EFF6FF` |
| Spacing | structured, medium density, 40 px outer margin |
| Typography | strong title 32-36 pt, body 17-19 pt, notes 10-11 pt |
| Cards | white cards, 1 px slate border, radius 8 |
| Icons | line icons, navy stroke, blue accent |
| Shapes | rectangles, bands, connectors, low shadow |
| Charts | clean axes, blue primary series, gray secondary |
| Photos | realistic office, system, or team images; avoid decorative blur |

### 3.2 Consulting

| Area | Definition |
|---|---|
| Use case | strategy, transformation, executive decision |
| Colors | charcoal `#111827`, royal blue `#1D4ED8`, cyan `#06B6D4`, off-white `#F8FAFC`, amber accent `#F59E0B` |
| Spacing | generous, strong whitespace, 48 px outer margin |
| Typography | headline 34-40 pt, body 17-18 pt, number 44-56 pt |
| Cards | thin border, small labels, crisp sections |
| Icons | minimal line icons, single accent color |
| Shapes | grids, matrices, pyramids, evidence stacks |
| Charts | data-first, clear labels, no decorative 3D |
| Photos | optional, cropped with high editorial quality |

### 3.3 Executive

| Area | Definition |
|---|---|
| Use case | board, CEO, investment decision |
| Colors | deep navy `#020617`, white `#FFFFFF`, cyan `#22D3EE`, silver `#CBD5E1`, green `#10B981` |
| Spacing | very generous, low density, 56 px outer margin |
| Typography | headline 38-46 pt, body 18-20 pt, metric 56-72 pt |
| Cards | few cards only, strong hierarchy |
| Icons | sparse, premium, consistent line width |
| Shapes | hero panels, executive scorecards, decision cards |
| Charts | big-number cards and simple trend lines |
| Photos | premium abstract business or product-related visuals |

### 3.4 Agency

| Area | Definition |
|---|---|
| Use case | brand, creative, marketing, campaign proposal |
| Colors | navy `#111827`, vivid blue `#3B82F6`, cyan `#06B6D4`, violet accent `#8B5CF6`, white |
| Spacing | dynamic, asymmetric, 40-56 px margin |
| Typography | headline 40-48 pt, body 17-19 pt, expressive labels |
| Cards | image-rich cards, large crops, radius 12 |
| Icons | line icons plus illustrative accents |
| Shapes | layered panels, image placeholders, diagonal crops |
| Charts | simple visual scorecards, avoid dense finance charts |
| Photos | high-impact campaign, product, or audience imagery |

### 3.5 Modern

| Area | Definition |
|---|---|
| Use case | SaaS, AI, DX, product proposal |
| Colors | white `#FFFFFF`, near-black `#0F172A`, blue `#2563EB`, cyan `#06B6D4`, gray `#E2E8F0` |
| Spacing | balanced, modular, 44 px margin |
| Typography | headline 34-42 pt, body 17-18 pt |
| Cards | soft border, subtle background, radius 10 |
| Icons | consistent line icons, simple filled accents |
| Shapes | product UI mock, process flow, architecture cards |
| Charts | KPI cards, clean bars, small trend lines |
| Photos | product screenshots or abstract system visuals |

### 3.6 Minimal

| Area | Definition |
|---|---|
| Use case | concise proposal, formal summary, low-distraction decks |
| Colors | white `#FFFFFF`, black `#111111`, gray `#6B7280`, blue accent `#2563EB` |
| Spacing | high whitespace, 56 px margin |
| Typography | headline 32-40 pt, body 17-18 pt, strong line height |
| Cards | minimal border or no card |
| Icons | very sparse line icons |
| Shapes | lines, dividers, simple tables |
| Charts | one chart per slide, no decoration |
| Photos | avoid unless directly useful |

### 3.7 Startup

| Area | Definition |
|---|---|
| Use case | new service, product launch, fast growth |
| Colors | ink `#0F172A`, blue `#2563EB`, green `#22C55E`, cyan `#06B6D4`, soft background `#F8FAFC` |
| Spacing | energetic but clean, 40 px margin |
| Typography | headline 38-46 pt, body 17-19 pt |
| Cards | bolder cards, light shadows, radius 12 |
| Icons | friendly line icons with filled badges |
| Shapes | flywheel, roadmap, feature cards |
| Charts | growth charts and KPI cards |
| Photos | product, user, or workflow visuals |

### 3.8 Investor

| Area | Definition |
|---|---|
| Use case | funding, business case, ROI, board investment |
| Colors | navy `#020617`, white `#FFFFFF`, gold `#F59E0B`, green `#10B981`, slate `#64748B` |
| Spacing | controlled, low density, 48 px margin |
| Typography | headline 34-42 pt, number 54-72 pt, body 17-18 pt |
| Cards | metric-first cards, strong contrast |
| Icons | financial and operational line icons |
| Shapes | ROI bridge, waterfall, scorecard, risk matrix |
| Charts | financial bridge, scenario comparison, trend lines |
| Photos | minimal; charts and business case visuals preferred |

---

## 4. Theme Selection Rules

| Condition | Recommended theme |
|---|---|
| CEO or board audience | Executive or Investor |
| Strategy consulting proposal | Consulting |
| Enterprise operations proposal | Corporate |
| SaaS or AI product proposal | Modern |
| Creative or marketing proposal | Agency |
| Short formal deck | Minimal |
| New product or growth initiative | Startup |
| ROI and investment decision | Investor |

---

## 5. Theme Validation

Theme output must be rejected when:

- color contrast is below accessibility threshold
- body text would fall below 17 pt in proposal slides
- theme proposes rasterized text
- theme requires external assets without license metadata
- theme changes slide message or facts
