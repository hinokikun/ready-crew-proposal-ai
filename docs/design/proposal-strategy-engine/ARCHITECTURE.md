# Proposal Strategy Engine Architecture

Version: 40.0
Status: Design only. No production implementation.

## 1. Position in ProposalPilot

```text
Input / CRM / Project History
-> Proposal Strategy Engine
-> Presentation Pack Selector
-> Presentation Engine
-> PPTX / PDF / Beautiful.ai
```

Proposal Strategy Engine is upstream of all presentation generation.

## 2. Boundary

### In Scope

- classify project type
- infer audience
- select proposal strategy
- select story order
- create normalized Strategy Brief
- define prohibited terms
- define evidence policy

### Out of Scope

- slide layout rendering
- PPTX XML creation
- DB persistence
- API routing
- authentication
- permissions
- Beautiful.ai API calls
- prompt execution

## 3. Logical Components

| Component | Responsibility |
|---|---|
| Project Interpreter | Extracts project type, delivery shape, constraints, and category signals. |
| Audience Interpreter | Estimates primary and secondary audiences. |
| Strategy Selector | Chooses dominant proposal strategy. |
| Story Planner | Maps story pack to page order and page messages. |
| Risk and Evidence Guard | Prevents unsupported facts, unsupported numbers, and category leakage. |
| Strategy Brief Builder | Produces the final handoff object for Presentation Engine. |

## 4. Data Contract

### Input: Project Strategy Input

```json
{
  "project_id": "project_x",
  "organization_id": "org_x",
  "workspace_id": "workspace_x",
  "project_title": "AI-OCR導入支援",
  "project_summary": "帳票画像から必要項目を抽出し、確認後に既存システムへ連携する",
  "industry": "manufacturing",
  "department": "operations",
  "objectives": ["manual workload reduction", "quality stabilization"],
  "constraints": {
    "budget": "upper limit only",
    "schedule": "target month only"
  },
  "known_facts": ["CSV連携", "人の最終確認あり"],
  "unknowns": ["current processing volume", "current error rate"]
}
```

### Output: Strategy Brief

```json
{
  "version": "strategy_brief_v1",
  "project_type_profile": {
    "primary_type": "vision_ocr",
    "secondary_type": "automation",
    "delivery_shape": "poc_then_implementation"
  },
  "audience_profile": {
    "primary_audience": "field_lead",
    "secondary_audience": ["department_director", "information_systems"],
    "decision_maker": "department_director"
  },
  "strategy_profile": {
    "primary_strategy": "quality_improvement",
    "secondary_strategy": "operation_efficiency",
    "priority_message": "AI候補提示と人の確認で品質を安定させる",
    "risk_message": "完全自動化を前提にせず、確認と修正を残す"
  },
  "story_blueprint": {
    "story_pack": "quality_story",
    "page_order": [
      "hero",
      "executive_summary",
      "current_problem",
      "before_after",
      "architecture",
      "poc_plan",
      "kpi_measurement",
      "estimate_next_action"
    ]
  },
  "presentation_input": {
    "presentation_pack": "vision_ocr",
    "kpi_pack": "quality_measurement",
    "estimate_pack": "poc_to_implementation",
    "architecture_type": "human_in_the_loop_ai",
    "hero_theme": "assisted_decision"
  },
  "guards": {
    "prohibited_terms": ["SEO", "CMS", "site map"],
    "evidence_policy": "do_not_invent_numbers",
    "human_review_required": false
  }
}
```

## 5. Presentation Engine Connection

Presentation Engine should consume only `presentation_input`, `story_blueprint`, and selected safe messages.

It should not:

- infer category again
- override persona
- invent KPI values
- inject category-specific vocabulary
- change strategic story order without a Strategy Brief update

## 6. Guardrails

| Risk | Guardrail |
|---|---|
| Web terms leak into OCR proposal | `prohibited_terms` enforced at Strategy Brief and Presentation validation. |
| Unsupported ROI appears | `evidence_policy` blocks fabricated numeric claims. |
| Executive proposal becomes too technical | Persona Pack controls page order and level of detail. |
| Field proposal becomes too abstract | Persona Pack moves workflow and operation pages earlier. |
| Compound project becomes confused | Primary and secondary project types are explicit. |

## 7. Audit Requirements for Future Implementation

If implemented later, the following should be auditable:

- selected strategy
- selected persona
- selected story pack
- selected presentation pack
- confidence
- human override
- prohibited terms
- evidence policy
- generated Strategy Brief version

## 8. Human Approval Before Implementation

This architecture should not be implemented until the following are approved:

- Strategy Brief schema
- Persona Pack definitions
- Story Pack definitions
- Decision Rules
- Presentation Engine integration contract
- validation and QA rules
