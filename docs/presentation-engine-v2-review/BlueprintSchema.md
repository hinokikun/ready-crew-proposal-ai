# Blueprint Schema

This document defines the implementation-grade JSON Schema for Presentation Engine 2.0.

---

## 1. Enums

### SlideGoal

```text
cover
agenda
executive_summary
problem_sharing
current_state
background
market_context
customer_insight
competitive_analysis
comparison
roi_explanation
kpi_definition
proposal_overview
solution_detail
architecture
process
roadmap
timeline
estimate
pricing
risk_handling
case_study
team
implementation_plan
faq
next_action
closing
appendix
```

### Audience

```text
ceo
executive
department_head
manager
field_leader
information_systems
finance
marketing
sales
hr
procurement
general
```

### VisualType

```text
hero
text_only
two_column
three_column
comparison_table
kpi_dashboard
timeline
roadmap
process_flow
architecture_map
matrix_2x2
pyramid
funnel
tree
swimlane
risk_matrix
heatmap
waterfall
bar_chart
line_chart
card_grid
quote
checklist
decision_tree
before_after
```

### Theme

```text
corporate
consulting
executive
modern
minimal
agency
startup
investor
```

### DiagramType

```text
none
process_flow
timeline
roadmap
comparison_matrix
kpi_dashboard
architecture_layer
feedback_loop
cycle
funnel
pyramid
tree
swimlane
risk_matrix
quadrant
heatmap
waterfall
org_chart
decision_tree
ecosystem_map
```

### AnimationHint

```text
none
step_by_step
fade_sequence
build_diagram
highlight_metric
reveal_comparison
```

---

## 2. Type Definitions

### Evidence

```json
{
  "type": "object",
  "required": ["evidence_type", "text", "confidence"],
  "properties": {
    "evidence_type": {
      "type": "string",
      "enum": ["provided", "derived", "assumption", "benchmark", "needs_confirmation"]
    },
    "text": {"type": "string", "minLength": 1, "maxLength": 400},
    "source_ref": {"type": "string", "maxLength": 120},
    "confidence": {
      "type": "string",
      "enum": ["high", "medium", "low", "needs_validation"]
    }
  }
}
```

### Hierarchy

```json
{
  "type": "object",
  "required": ["primary", "secondary", "gaze_path", "density"],
  "properties": {
    "primary": {"type": "string"},
    "secondary": {"type": "array", "items": {"type": "string"}},
    "tertiary": {"type": "array", "items": {"type": "string"}},
    "gaze_path": {"type": "array", "minItems": 2, "items": {"type": "string"}},
    "density": {"type": "string", "enum": ["low", "medium", "high"]},
    "emphasis_tokens": {"type": "array", "items": {"type": "string"}}
  }
}
```

### Typography

```json
{
  "type": "object",
  "required": ["headline_pt", "body_pt", "number_pt", "note_pt"],
  "properties": {
    "headline_pt": {"type": "integer", "minimum": 28, "maximum": 56},
    "body_pt": {"type": "integer", "minimum": 16, "maximum": 24},
    "number_pt": {"type": "integer", "minimum": 32, "maximum": 60},
    "note_pt": {"type": "integer", "minimum": 10, "maximum": 13},
    "font_family": {"type": "string"},
    "line_height": {"type": "number", "minimum": 1.0, "maximum": 1.6}
  }
}
```

### Layout

```json
{
  "type": "object",
  "required": ["grid", "safe_area", "zones"],
  "properties": {
    "grid": {
      "type": "object",
      "properties": {
        "columns": {"type": "integer", "minimum": 4, "maximum": 24},
        "rows": {"type": "integer", "minimum": 4, "maximum": 16},
        "gutter": {"type": "number"}
      }
    },
    "safe_area": {
      "type": "object",
      "required": ["x", "y", "width", "height"],
      "properties": {
        "x": {"type": "number"},
        "y": {"type": "number"},
        "width": {"type": "number"},
        "height": {"type": "number"}
      }
    },
    "zones": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["zone_id", "role", "x", "y", "width", "height"],
        "properties": {
          "zone_id": {"type": "string"},
          "role": {"type": "string"},
          "x": {"type": "number"},
          "y": {"type": "number"},
          "width": {"type": "number"},
          "height": {"type": "number"}
        }
      }
    }
  }
}
```

### DiagramDefinition

```json
{
  "type": "object",
  "required": ["diagram_type", "items"],
  "properties": {
    "diagram_type": {"type": "string"},
    "items": {"type": "array"},
    "nodes": {"type": "array"},
    "edges": {"type": "array"},
    "axes": {"type": "array"},
    "series": {"type": "array"},
    "reading_order": {"type": "array", "items": {"type": "string"}},
    "emphasis": {"type": "array", "items": {"type": "string"}}
  }
}
```

---

## 3. Top-Level Blueprint Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PresentationEngineV2Blueprint",
  "type": "object",
  "required": ["schema_version", "deck", "slides", "quality_requirements", "metadata"],
  "properties": {
    "schema_version": {
      "type": "string",
      "const": "presentation_engine_v2_blueprint_1"
    },
    "deck": {
      "type": "object",
      "required": ["title", "audience", "theme", "story_type", "main_decision"],
      "properties": {
        "title": {"type": "string", "minLength": 1, "maxLength": 120},
        "audience": {"type": "string"},
        "theme": {"type": "string"},
        "story_type": {"type": "string"},
        "main_decision": {"type": "string", "maxLength": 240}
      }
    },
    "slides": {
      "type": "array",
      "minItems": 1,
      "maxItems": 40,
      "items": {"$ref": "#/$defs/slide"}
    },
    "quality_requirements": {
      "type": "object",
      "required": ["editable_shapes", "numeric_integrity", "human_review_required"],
      "properties": {
        "editable_shapes": {"type": "boolean"},
        "numeric_integrity": {"type": "boolean"},
        "human_review_required": {"type": "boolean"},
        "font_floor_pt": {"type": "integer", "minimum": 10},
        "body_font_floor_pt": {"type": "integer", "minimum": 16}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "source": {"type": "string"},
        "created_by": {"type": "string"},
        "external_assets": {"type": "array"},
        "warnings": {"type": "array", "items": {"type": "string"}}
      }
    }
  },
  "$defs": {
    "slide": {
      "type": "object",
      "required": [
        "slide_id",
        "slide_goal",
        "audience",
        "headline",
        "main_message",
        "supporting_evidence",
        "visual_type",
        "layout",
        "theme",
        "hierarchy",
        "color_palette",
        "typography",
        "diagram_definition",
        "cta",
        "animation_hint",
        "rendering_metadata"
      ],
      "properties": {
        "slide_id": {"type": "string"},
        "slide_goal": {"type": "string"},
        "audience": {"type": "string"},
        "headline": {"type": "string", "minLength": 1, "maxLength": 90},
        "main_message": {"type": "string", "minLength": 1, "maxLength": 240},
        "supporting_evidence": {"type": "array"},
        "visual_type": {"type": "string"},
        "layout": {"type": "object"},
        "theme": {"type": "object"},
        "hierarchy": {"type": "object"},
        "color_palette": {"type": "object"},
        "typography": {"type": "object"},
        "diagram_definition": {"type": "object"},
        "cta": {"type": "string", "maxLength": 120},
        "animation_hint": {"type": "string"},
        "rendering_metadata": {"type": "object"}
      }
    }
  }
}
```

---

## 4. Missing Items from Current Blueprint.md

- Strict enum definitions
- Layout zone coordinates
- Grid definition
- Shape role metadata
- Font floors
- Evidence confidence
- Safe fallback metadata
- Numeric token preservation list
- Human review item list
- Renderer warning field

---

## 5. Required Enum Bindings

The implementation schema must bind string fields to enum definitions. Free-form strings are not allowed for core renderer decisions.

```json
{
  "$defs": {
    "SlideGoal": {
      "type": "string",
      "enum": [
        "cover",
        "agenda",
        "executive_summary",
        "problem_sharing",
        "current_state",
        "background",
        "market_context",
        "customer_insight",
        "competitive_analysis",
        "comparison",
        "roi_explanation",
        "kpi_definition",
        "proposal_overview",
        "solution_detail",
        "architecture",
        "process",
        "roadmap",
        "timeline",
        "estimate",
        "pricing",
        "risk_handling",
        "case_study",
        "team",
        "implementation_plan",
        "faq",
        "next_action",
        "closing",
        "appendix"
      ]
    },
    "VisualType": {
      "type": "string",
      "enum": [
        "hero",
        "text_only",
        "two_column",
        "three_column",
        "comparison_table",
        "kpi_dashboard",
        "timeline",
        "roadmap",
        "process_flow",
        "architecture_map",
        "matrix_2x2",
        "pyramid",
        "funnel",
        "tree",
        "swimlane",
        "risk_matrix",
        "heatmap",
        "chart",
        "image_placeholder",
        "quote",
        "closing"
      ]
    },
    "Theme": {
      "type": "string",
      "enum": [
        "corporate",
        "consulting",
        "executive",
        "agency",
        "modern",
        "minimal",
        "startup",
        "investor"
      ]
    },
    "DiagramType": {
      "type": "string",
      "enum": [
        "none",
        "linear_timeline",
        "roadmap_lanes",
        "process_flow",
        "swimlane_process",
        "before_after_flow",
        "matrix_2x2",
        "risk_matrix",
        "comparison_table",
        "kpi_dashboard",
        "layered_architecture",
        "data_flow",
        "system_integration_map",
        "ai_pipeline",
        "human_in_the_loop",
        "feedback_loop",
        "maturity_model",
        "stakeholder_map",
        "roi_bridge",
        "cost_breakdown",
        "next_action_board"
      ]
    },
    "AnimationHint": {
      "type": "string",
      "enum": [
        "none",
        "appear_by_section",
        "appear_by_step",
        "highlight_main_message",
        "build_timeline",
        "build_process",
        "fade_supporting_evidence"
      ]
    }
  }
}
```

The implementation may include more diagram enum values, but every value must map to a catalog item in `DiagramCatalog.md`.

---

## 6. Renderer-ready Layout Object

Each slide `layout` object must include enough information for drawing without inference:

```json
{
  "layout": {
    "layout_id": "L-020",
    "layout_name": "before_after_flow",
    "grid": {
      "columns": 12,
      "rows": 8,
      "margin": {"top": 0.42, "right": 0.48, "bottom": 0.42, "left": 0.48},
      "gutter": 0.16
    },
    "zones": [
      {
        "zone_id": "headline",
        "role": "headline",
        "x": 0.06,
        "y": 0.08,
        "w": 0.88,
        "h": 0.14
      }
    ],
    "safe_area": {"x": 0.04, "y": 0.05, "w": 0.92, "h": 0.88},
    "z_order_policy": "background_to_foreground"
  }
}
```

---

## 7. Numeric Integrity Metadata

Every numeric value that appears in rendered text, charts, estimates, KPI cards, or tables must be listed:

```json
{
  "numeric_integrity": {
    "tokens": [
      {
        "token_id": "n-001",
        "value": "1,000万円",
        "source": "user_input",
        "may_transform": false,
        "render_locations": ["slide-08.estimate_card_01"]
      }
    ]
  }
}
```

Renderer validation must fail if a `may_transform=false` value is changed.
