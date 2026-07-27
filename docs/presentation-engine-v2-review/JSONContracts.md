# JSON Contracts

This document defines input and output contracts between Presentation Engine 2.0 components. These contracts are implementation boundaries, not UI or API endpoints.

---

## 1. Contract Principles

- Each component consumes only the previous approved contract.
- Each component outputs only its owned fields.
- No component may mutate upstream output.
- The Blueprint Assembler may combine outputs but may not invent missing facts.
- The Renderer accepts only `PresentationBlueprint`.

---

## 2. Common Types

```json
{
  "component_metadata": {
    "component": "message_designer_ai",
    "schema_version": "1.0",
    "confidence": 0.84,
    "human_review_required": false,
    "warnings": []
  }
}
```

---

## 3. Slide Intent AI

### Input

```json
{
  "slide_id": "slide-03",
  "story_context": {
    "deck_goal": "win approval for PoC",
    "audience": "department_head",
    "story_type": "ai_adoption"
  },
  "draft_slide": {
    "title": "Current issues",
    "content_items": []
  }
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "slide_goal": "current_state",
  "slide_type_id": "S013",
  "success_criteria": [
    "Audience understands the current workflow."
  ],
  "split_recommended": false,
  "component_metadata": {}
}
```

---

## 4. Message Designer AI

### Input

```json
{
  "slide_id": "slide-03",
  "intent": {},
  "raw_content": [],
  "evidence": []
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "headline": "Manual checking creates delays and inconsistent quality.",
  "main_message": "The current process depends on human visual checks, which creates delay, variation, and limited reuse of judgment history.",
  "supporting_points": [],
  "cut_items": [],
  "emphasis_targets": ["delay", "quality variation"],
  "assumptions": [],
  "component_metadata": {}
}
```

---

## 5. White Space Optimizer

### Input

```json
{
  "slide_id": "slide-03",
  "message_plan": {},
  "content_metrics": {
    "headline_chars": 48,
    "body_chars": 320,
    "bullet_count": 5,
    "data_points": 3
  }
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "density": "medium",
  "fit_action": "diagramize",
  "split_recommended": false,
  "compression_required": false,
  "max_body_chars": 260,
  "component_metadata": {}
}
```

---

## 6. Visual Director AI

### Input

```json
{
  "slide_id": "slide-03",
  "intent": {},
  "message_plan": {},
  "density_plan": {},
  "available_diagrams": ["process_flow", "issue_cluster", "swimlane_process"]
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "visual_type": "process_flow",
  "diagram_type": "process_flow",
  "reason": "The slide explains a sequence of current operations.",
  "alternative_visuals": ["swimlane_process", "issue_cluster"],
  "component_metadata": {}
}
```

---

## 7. Diagram Composer

### Input

```json
{
  "slide_id": "slide-03",
  "visual_plan": {},
  "message_plan": {},
  "content_items": []
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "diagram_definition": {
    "diagram_type": "process_flow",
    "nodes": [],
    "connectors": [],
    "groups": [],
    "labels": [],
    "reading_order": []
  },
  "component_metadata": {}
}
```

---

## 8. Hierarchy Engine

### Input

```json
{
  "slide_id": "slide-03",
  "message_plan": {},
  "visual_plan": {},
  "diagram_definition": {}
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "hierarchy": {
    "level_1": ["headline"],
    "level_2": ["current_flow"],
    "level_3": ["issue_annotations"],
    "gaze_path": ["headline", "flow_start", "issue_callouts", "conclusion"],
    "zones": []
  },
  "component_metadata": {}
}
```

---

## 9. Theme Engine

### Input

```json
{
  "deck_context": {
    "audience": "department_head",
    "tone": "consulting",
    "brand": "ProposalPilot"
  },
  "hierarchy": {}
}
```

### Output

```json
{
  "theme": {
    "theme_id": "consulting",
    "color_palette": {},
    "spacing": {},
    "cards": {},
    "icons": {},
    "charts": {},
    "photos": {}
  },
  "component_metadata": {}
}
```

---

## 10. Typography Engine

### Input

```json
{
  "slide_id": "slide-03",
  "theme": {},
  "hierarchy": {},
  "density_plan": {}
}
```

### Output

```json
{
  "slide_id": "slide-03",
  "typography": {
    "headline": {"font": "Noto Sans JP", "size_pt": 36, "weight": 700},
    "body": {"font": "Noto Sans JP", "size_pt": 18, "weight": 400},
    "note": {"font": "Noto Sans JP", "size_pt": 11, "weight": 400},
    "number": {"font": "Inter", "size_pt": 52, "weight": 700}
  },
  "component_metadata": {}
}
```

---

## 11. Blueprint Assembler

### Input

```json
{
  "intent_outputs": [],
  "message_outputs": [],
  "density_outputs": [],
  "visual_outputs": [],
  "diagram_outputs": [],
  "hierarchy_outputs": [],
  "theme_output": {},
  "typography_outputs": []
}
```

### Output

```json
{
  "schema_version": "presentation_engine_v2_blueprint_1",
  "deck": {},
  "slides": [],
  "quality_requirements": {},
  "metadata": {}
}
```

---

## 12. Renderer Contract

### Input

Only:

```json
{
  "presentation_blueprint": {}
}
```

### Output

```json
{
  "render_result": {
    "status": "success",
    "pptx_path": "local/path/proposal.pptx",
    "warnings": [],
    "render_metadata": {
      "slide_count": 12,
      "editable_shapes": true,
      "external_references": []
    }
  }
}
```

### Error Output

```json
{
  "render_result": {
    "status": "error",
    "error_code": "TEXT_OVERFLOW",
    "slide_id": "slide-04",
    "message": "Body text cannot fit at minimum font size.",
    "safe_to_retry": false
  }
}
```

---

## 13. Contract Test Requirements

- Each component output validates against its schema.
- Each component refuses fields owned by another component.
- Blueprint Assembler rejects missing required fields.
- Renderer rejects invalid blueprint before drawing.
- Renderer output contains no AI-derived changes.
