# Rendering Rules

Rendering Rules define how PowerPoint Renderer should consume a Blueprint.

---

## Core Rules

1. Render only from Blueprint.
2. Do not reinterpret strategy.
3. Do not invent numbers.
4. Preserve numeric tokens.
5. Render diagrams as editable shapes.
6. Keep body text at 16 pt or larger unless explicitly marked as note.
7. Prevent overlap and clipping.
8. Preserve source trace and assumptions.
9. Use safe fallback if a visual type is unsupported.
10. Report all fallbacks in Quality Report.

---

## Fallback Rules

| Unsupported Item | Fallback |
|---|---|
| Complex diagram | Simplified editable flow |
| Too many table columns | Split table |
| Too much body text | Split slide |
| Unknown theme | Corporate |
| Unknown visual type | Title + message + evidence |
| Low confidence | Human review required |

---

## Quality Gates

| Gate | Requirement |
|---|---|
| Structural | Valid Blueprint JSON |
| Narrative | Every slide has one main message |
| Visual | Every slide has visual_type |
| Typography | Minimum font rules satisfied |
| Numeric | Numeric Integrity preserved |
| Safety | No secrets in blueprint |
| Rendering | No clipping or unintended overlap |

