# Blueprint

The Blueprint is the contract between Presentation Engine 2.0 and the PowerPoint Renderer.

It is not a PPTX file. It is a structured design plan.

---

## Slide Blueprint Fields

Each slide must contain:

| Field | Meaning |
|---|---|
| `slide_goal` | Why the slide exists |
| `audience` | Primary reader or decision maker |
| `headline` | Audience-facing takeaway title |
| `main_message` | The one message the slide should communicate |
| `supporting_evidence` | Evidence, facts, assumptions, or examples |
| `visual_type` | Best visual expression |
| `layout` | Layout structure and zones |
| `theme` | Theme token reference |
| `hierarchy` | Importance, size, and gaze path |
| `color_palette` | Role-based colors |
| `typography` | Title, body, number, note styles |
| `diagram_definition` | Editable diagram structure |
| `cta` | Desired next action |
| `animation_hint` | Optional motion intent |
| `rendering_metadata` | Renderer-safe metadata |

---

## Example

```json
{
  "slide_goal": "ROI explanation",
  "audience": "executive",
  "headline": "提案作成時間を削減し、営業品質を標準化します",
  "main_message": "AIが営業担当者の判断を支援し、提案準備の時間とばらつきを減らします。",
  "supporting_evidence": [
    {
      "type": "input_fact",
      "text": "現在の提案書初稿作成は2〜4時間",
      "confidence": "provided"
    },
    {
      "type": "assumption",
      "text": "削減効果はPoCで実測",
      "confidence": "needs_validation"
    }
  ],
  "visual_type": "kpi_dashboard",
  "layout": {
    "structure": "headline_top_metrics_middle_actions_bottom",
    "zones": ["headline", "metric_cards", "evidence_note", "next_action"]
  },
  "theme": "executive_consulting",
  "hierarchy": {
    "primary": "time_reduction",
    "secondary": ["quality_standardization", "review_load"],
    "gaze_path": ["headline", "main_metric", "supporting_metrics", "next_action"]
  },
  "color_palette": {
    "background": "white",
    "primary": "navy",
    "accent": "cyan",
    "warning": "amber"
  },
  "typography": {
    "headline_pt": 34,
    "body_pt": 18,
    "number_pt": 44,
    "note_pt": 11
  },
  "diagram_definition": {
    "type": "metric_cards",
    "items": [
      {"label": "使用前", "value": "2〜4時間", "status": "current"},
      {"label": "使用後", "value": "PoCで測定", "status": "target"}
    ]
  },
  "cta": "PoC対象案件を3件選定する",
  "animation_hint": "none",
  "rendering_metadata": {
    "editable_shapes": true,
    "numeric_integrity_required": true,
    "source_trace_required": true
  }
}
```

---

## Blueprint Rules

- No field may contain API keys, tokens, passwords, or private URLs.
- Numbers must preserve source values.
- Assumptions must be marked as assumptions.
- If evidence is missing, the slide must say what needs confirmation.
- Renderer may simplify visuals for safety, but must not alter meaning.

