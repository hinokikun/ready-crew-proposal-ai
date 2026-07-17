# Proposal Strategy Engine

Version: 40.0
Status: Design only. No production implementation.

## 1. Definition

Proposal Strategy Engine is the pre-presentation reasoning layer for ProposalPilot.

It decides:

- what to communicate
- who the proposal is for
- which concern should be addressed first
- which story pattern should be used
- which evidence and risk framing should be emphasized
- what the Presentation Engine may and may not say

It does not create final slide design. That remains the responsibility of the Presentation Engine.

## 2. Five-Layer Model

| Layer | Name | Main question | Output |
|---|---|---|---|
| Layer 1 | 案件理解 | What kind of project is this? | Project Type Profile |
| Layer 2 | 顧客理解 | Who must be persuaded? | Audience Profile |
| Layer 3 | 提案戦略 | What strategy should lead the proposal? | Strategy Profile |
| Layer 4 | ストーリー生成 | What order makes the proposal persuasive? | Story Blueprint |
| Layer 5 | Presentation入力 | What should be handed to Presentation Engine? | Strategy Brief |

## 3. Layer 1: 案件理解

### Input

- 案件概要
- 業界
- 目的
- 課題
- 提案内容
- 納品物
- スケジュール
- 予算
- 既存システム
- 連携対象
- 制約条件

### Responsibility

Layer 1 classifies the project before visual or story decisions are made.

### Judgment Content

| Judgment | Examples |
|---|---|
| 案件タイプ | AI導入, Web制作, DX, RPA, CRM, OCR, 生成AI, 複合案件, 汎用 |
| Complexity | single-domain, compound, exploratory |
| Delivery shape | PoC, pilot, implementation, migration, advisory, operation |
| Evidence level | explicit data, partial data, assumptions, unknown |
| Risk level | low, medium, high |

### Output: Project Type Profile

```json
{
  "project_type": "vision_ocr",
  "secondary_project_type": "automation",
  "delivery_shape": "poc_then_implementation",
  "budget_clarity": "upper_limit",
  "schedule_clarity": "target_month",
  "evidence_level": "partial",
  "risk_level": "medium",
  "prohibited_terms": ["SEO", "CMS", "site map"]
}
```

### Relationship With Other Layers

Layer 1 constrains every later decision. If the project is OCR, Story Pack and Presentation Pack must not inject Web or CRM terms unless those terms appear in the project input.

## 4. Layer 2: 顧客理解

### Input

- Project Type Profile
- department terms in the project
- job titles if present
- approval process if present
- budget owner if present
- operational user if present

### Responsibility

Layer 2 estimates the audience and decision structure.

### Judgment Content

| Judgment | Meaning |
|---|---|
| Primary Audience | Main reader or meeting owner |
| Secondary Audience | People who will influence evaluation |
| Decision Maker | Person or group that approves spend |
| Operator | Person or team that must use the result |
| Risk Owner | Person accountable for failure |

### Output: Audience Profile

```json
{
  "primary_audience": "department_director",
  "secondary_audience": ["field_lead", "information_systems"],
  "decision_maker": "executive",
  "operator": "quality_control",
  "risk_owner": "operations_manager",
  "persona_pack": "department_director"
}
```

### Relationship With Other Layers

Layer 2 changes the story order. CEO and executive audiences should see investment meaning early. Field audiences should see workflow and operational fit early.

## 5. Layer 3: 提案戦略

### Input

- Project Type Profile
- Audience Profile
- customer pain
- budget constraints
- schedule constraints
- project objective
- current failure mode

### Responsibility

Layer 3 selects the dominant proposal strategy.

### Strategy Types

| Strategy | Best when | Avoid when |
|---|---|---|
| ROI重視 | budget approval and investment return are central | no benefit baseline exists |
| 業務改善重視 | process burden is visible | issue is mainly brand or user experience |
| 品質改善重視 | error, inconsistency, inspection, or rework matter | quality is not a known concern |
| リスク低減 | failure, compliance, continuity, security matter | customer wants bold growth story |
| DX推進 | cross-department change is needed | project is narrow single-task automation |
| AI活用 | AI is the core mechanism and customer expects AI narrative | AI is only an implementation detail |
| 競争優位 | market differentiation or customer experience matters | internal-only operation improvement |
| コスト削減 | labor time, outsourcing, or rework cost are important | value is strategic rather than cost-based |
| スピード重視 | launch timing or backlog is urgent | careful governance is more important |

### Output: Strategy Profile

```json
{
  "primary_strategy": "quality_improvement",
  "secondary_strategy": "operation_efficiency",
  "priority_message": "AIが置き換えるのではなく、人の判断を支援する",
  "risk_message": "完全自動化ではなく確認プロセスを残す",
  "decision_focus": ["accuracy", "review_time", "field_fit"],
  "avoid_focus": ["unproven_full_automation", "unsupported_roi_numbers"]
}
```

### Relationship With Other Layers

Layer 3 controls what appears in the first half of the proposal. If strategy is quality improvement, the problem and KPI pages should show quality variance, error reduction, and review process. If strategy is ROI, those same pages should frame investment return and payback logic.

## 6. Layer 4: ストーリー生成

### Input

- Strategy Profile
- Audience Profile
- Project Type Profile
- requested page count
- required output format

### Responsibility

Layer 4 chooses a story pattern and maps messages to pages.

### Story Branch Examples

#### Executive Story

```text
Issue
-> investment meaning
-> risk and mitigation
-> roadmap
-> decision
```

#### Field Story

```text
Issue
-> workflow
-> assistance model
-> operation screen
-> PoC
```

#### IT Story

```text
Issue
-> architecture
-> integration
-> governance
-> operation
-> rollout
```

### Output: Story Blueprint

```json
{
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
  ],
  "page_messages": {
    "hero": "品質判断を標準化し、現場の確認を速くする",
    "before_after": "AI候補提示と人の最終確認で運用を崩さない"
  }
}
```

## 7. Layer 5: Presentation入力

### Input

- Project Type Profile
- Audience Profile
- Strategy Profile
- Story Blueprint

### Responsibility

Layer 5 creates the normalized handoff object for Presentation Engine.

### Output: Strategy Brief

```json
{
  "hero_theme": "assisted_decision",
  "main_message": "品質判断を標準化し、現場の確認を速くする",
  "problem_theme": "manual_variance",
  "architecture_type": "human_in_the_loop_ai",
  "presentation_pack": "vision_ocr",
  "kpi_pack": "quality_measurement",
  "estimate_pack": "poc_to_implementation",
  "priority_message": "AI候補提示と人の確認を両立する",
  "risk_message": "完全自動化を前提にしない",
  "next_action": "PoC評価基準と対象カテゴリを合意する",
  "persona_pack": "field_lead",
  "story_pack": "quality_story",
  "prohibited_terms": ["SEO", "CMS", "site map"],
  "evidence_policy": "do_not_invent_numbers"
}
```

## 8. Engine Non-Goals

Proposal Strategy Engine must not:

- generate final visual layout
- decide colors or typography
- create DB records
- call external APIs
- override permissions
- invent customer facts
- invent ROI numbers
- inject category terms that were not selected
- bypass Quality Gate

## 9. Approval Criteria Before Implementation

- Layer responsibilities are accepted.
- Strategy Brief schema is accepted.
- Persona Pack and Story Pack are sufficient for v1.1 production use.
- Fallback behavior is safe.
- Presentation Engine can use the Strategy Brief without business reasoning.
- Human review can override strategy when needed.
