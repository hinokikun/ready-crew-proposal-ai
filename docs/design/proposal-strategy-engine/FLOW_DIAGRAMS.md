# Proposal Strategy Engine Flow Diagrams

Version: 40.0
Status: Design only. No production implementation.

## 1. Overall Flow

```mermaid
flowchart LR
  A["案件情報"] --> B["Layer 1: 案件理解"]
  B --> C["Layer 2: 顧客理解"]
  C --> D["Layer 3: 提案戦略"]
  D --> E["Layer 4: ストーリー生成"]
  E --> F["Layer 5: Presentation入力"]
  F --> G["Presentation Pack選択"]
  G --> H["Presentation Engine"]
  H --> I["PPTX / PDF / Beautiful.ai"]
```

## 2. Five-Layer Structure

```mermaid
flowchart TB
  subgraph Engine["Proposal Strategy Engine"]
    L1["Layer 1 案件理解<br/>Project Type Profile"]
    L2["Layer 2 顧客理解<br/>Audience Profile"]
    L3["Layer 3 提案戦略<br/>Strategy Profile"]
    L4["Layer 4 ストーリー生成<br/>Story Blueprint"]
    L5["Layer 5 Presentation入力<br/>Strategy Brief"]
  end
  L1 --> L2 --> L3 --> L4 --> L5
```

## 3. Decision Flow

```mermaid
flowchart TD
  S["案件概要・目的・課題・納品物"] --> C1{"カテゴリ信号は強いか"}
  C1 -- "Yes" --> P1["Primary Presentation Packを選択"]
  C1 -- "No" --> P2["Generic Consulting Pack"]
  P1 --> A1{"主な読者は誰か"}
  P2 --> A1
  A1 -->|経営層| ST1["ROI / DX Story"]
  A1 -->|現場| ST2["Automation / Quality / AI Story"]
  A1 -->|情シス| ST3["DX / AI / Architecture-heavy Story"]
  A1 -->|営業| ST4["Customer Experience / CRM Story"]
  ST1 --> G["Guard: 根拠不明数値を禁止"]
  ST2 --> G
  ST3 --> G
  ST4 --> G
  G --> B["Strategy Briefを生成"]
```

## 4. Persona and Story Interaction

```mermaid
flowchart LR
  Persona["Persona Pack"] --> Order["説明順"]
  Strategy["Strategy Profile"] --> Message["優先メッセージ"]
  Project["Project Type Profile"] --> Pack["Presentation Pack"]
  Order --> Blueprint["Story Blueprint"]
  Message --> Blueprint
  Pack --> Brief["Strategy Brief"]
  Blueprint --> Brief
```

## 5. Presentation Engine Contract

```mermaid
sequenceDiagram
  participant Input as Project Input
  participant Strategy as Proposal Strategy Engine
  participant Pack as Pack Selector
  participant Presentation as Presentation Engine
  participant Output as PPTX/PDF/Beautiful.ai

  Input->>Strategy: project summary, constraints, known facts
  Strategy->>Strategy: classify project, audience, strategy, story
  Strategy->>Pack: primary type, secondary type, prohibited terms
  Pack-->>Strategy: presentation pack, KPI pack, estimate pack
  Strategy->>Presentation: Strategy Brief
  Presentation->>Presentation: render only from Strategy Brief
  Presentation->>Output: generate artifacts
```

## 6. Guardrail Flow

```mermaid
flowchart TD
  B["Strategy Brief"] --> T["Term Isolation Check"]
  T --> E["Evidence Check"]
  E --> P["Persona Fit Check"]
  P --> R{"Human review required?"}
  R -- "No" --> O["Presentation Engineへ渡す"]
  R -- "Yes" --> H["人がStrategyを確認"]
```

## 7. Compound Project Handling

```mermaid
flowchart TD
  X["複合案件"] --> Q1{"価値の中心はどこか"}
  Q1 -- "抽出・認識" --> V["Vision / OCR primary"]
  Q1 -- "業務自動化" --> A["Automation primary"]
  Q1 -- "顧客管理" --> C["CRM primary"]
  Q1 -- "知識検索" --> K["Knowledge AI primary"]
  V --> S["Secondary Packを下流工程として追加"]
  A --> S
  C --> S
  K --> S
  S --> G["Storyは1つに絞る"]
```
