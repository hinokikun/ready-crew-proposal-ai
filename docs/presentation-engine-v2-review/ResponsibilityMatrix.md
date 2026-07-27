# Responsibility Matrix

---

## 1. Component Boundary Summary

| Component | Owns | Does Not Own | Input | Output |
|---|---|---|---|---|
| Slide Intent AI | Slide purpose | Wording, layout, theme | Story outline, draft slide | Intent map |
| Message Designer AI | Headline, main message, keep/cut/emphasize | Diagram type, typography, rendering | Intent map, raw content, evidence | Message plan |
| White Space Optimizer | Density, compression, split decisions | Final visual expression | Message plan, content volume | Density plan |
| Visual Director AI | Visual type selection | Diagram internals, exact coordinates | Message plan, intent, density | Visual plan |
| Diagram Composer | Diagram structure | Theme colors, typography scale | Visual plan, content items | Diagram definition |
| Hierarchy Engine | Importance order, gaze path, zones | Font family, final rendering | Message, visual, diagram | Hierarchy plan |
| Typography Engine | Type scale and text role mapping | Slide meaning, message | Hierarchy, theme | Typography tokens |
| Theme Engine | Visual language tokens | Slide strategy, diagram logic | Audience, story, hierarchy | Theme tokens |
| Blueprint Assembler | Valid JSON blueprint | AI reasoning | All component outputs | Rendering Blueprint |
| PowerPoint Renderer | Draw editable PPTX shapes | AI decisions, message rewriting | Rendering Blueprint | PPTX |

---

## 2. Strict Boundary Rules

### Slide Intent AI

- Decides: "This slide exists to explain ROI."
- Does not decide: "Use KPI cards."
- Does not rewrite: headline or body.

### Message Designer AI

- Decides: "The main message is time reduction plus quality standardization."
- Cuts: redundant text and low-value details.
- Does not decide: exact visual type or font size.

### White Space Optimizer

- Decides: "Split this slide into two slides."
- Does not decide: diagram type unless split requires visual recommendation.

### Visual Director AI

- Decides: "Use KPI dashboard instead of bullets."
- Does not define nodes and connectors.

### Diagram Composer

- Designs node/edge/table/matrix structure.
- Does not pick theme colors.

### Hierarchy Engine

- Decides: "Main metric is Level 1, proof is Level 2."
- Does not set final font sizes.

### Typography Engine

- Converts hierarchy into font size, weight, line height.
- Does not change message.

### Theme Engine

- Provides theme tokens.
- Does not alter slide intent or message.

### Renderer

- Draws only.
- Must not call AI.
- Must not choose visual type.
- Must not invent or change numbers.
- Must not rewrite text.

---

## 3. RACI Matrix

| Decision | Intent | Message | White Space | Visual | Diagram | Hierarchy | Typography | Theme | Renderer |
|---|---|---|---|---|---|---|---|---|---|
| Slide goal | R | C | I | I | I | I | I | I | I |
| Headline | C | R | C | I | I | I | I | I | I |
| Content deletion | I | R | C | I | I | I | I | I | I |
| Slide split | C | C | R | C | I | I | I | I | I |
| Visual type | C | C | C | R | C | I | I | I | I |
| Diagram nodes | I | C | I | C | R | C | I | I | I |
| Gaze path | I | C | C | C | C | R | C | I | I |
| Font sizes | I | I | C | I | I | C | R | C | I |
| Theme | I | I | I | C | I | C | C | R | I |
| Coordinates | I | I | I | I | C | C | C | C | R |
| Shape rendering | I | I | I | I | I | I | I | I | R |

R = Responsible, C = Consulted, I = Informed.

---

## 4. Duplicate Responsibility Risks

| Risk | Cause | Resolution |
|---|---|---|
| Intent vs Slide Type confusion | Slide Intent AI could become keyword classifier | Use intent enum and success criteria |
| Message vs Visual overlap | Message AI may choose diagrams | Message AI can suggest emphasis, but Visual AI selects visual type |
| Hierarchy vs Typography overlap | Both touch size | Hierarchy defines levels, Typography maps levels to size |
| Theme vs Renderer overlap | Renderer may hardcode colors | Renderer must use theme tokens only |
| Diagram vs Renderer overlap | Renderer may infer diagram | Diagram Composer defines structure; Renderer draws it |

