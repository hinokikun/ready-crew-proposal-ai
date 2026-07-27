# Rendering Blueprint

Rendering Blueprint is the final JSON produced by Presentation Engine 2.0.

It is renderer-ready, but not renderer-specific.

---

## Top-Level Schema

```json
{
  "schema_version": "presentation_engine_v2_blueprint_1",
  "deck": {
    "title": "string",
    "audience": "string",
    "theme": "string",
    "story_type": "string",
    "main_decision": "string"
  },
  "slides": [],
  "quality_requirements": {
    "editable_shapes": true,
    "numeric_integrity": true,
    "human_review_required": false
  },
  "metadata": {
    "source": "strategy_v1",
    "created_by": "presentation_engine_v2",
    "external_assets": []
  }
}
```

---

## Slide Schema

```json
{
  "slide_id": "slide-01",
  "slide_goal": "Problem Sharing",
  "audience": "executive",
  "headline": "提案作成の属人化が営業品質を左右しています",
  "main_message": "AI支援により、準備時間と品質差を同時に改善できます。",
  "supporting_evidence": [],
  "visual_type": "process_flow",
  "layout": {},
  "theme": {},
  "hierarchy": {},
  "color_palette": {},
  "typography": {},
  "diagram_definition": {},
  "cta": "",
  "animation_hint": "none",
  "rendering_metadata": {}
}
```

---

## Rendering Metadata

| Field | Purpose |
|---|---|
| `editable_shapes` | Must render as editable shapes |
| `safe_fallback` | Fallback visual if layout unsupported |
| `numeric_tokens` | Numbers that must be preserved |
| `source_trace` | Evidence source labels |
| `human_review_items` | Items requiring confirmation |
| `overflow_policy` | Compress, split, or fail |
| `font_floor_pt` | Minimum font size |

