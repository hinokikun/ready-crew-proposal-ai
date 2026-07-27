# Data Model Design

## Current Entities

`backend/app/database/schema.py`にはOrganization、Workspace、User、Customer、Project、Proposal History、Business Improvement、Proposal Agent Memory、Usage/Audit Logs、Knowledge、Templates、Quality Gates、Beautiful.ai Presentations、Presentation Review、Proposal Optimizationなどが存在する。

## Future Entities

```mermaid
erDiagram
  ORGANIZATION ||--o{ WORKSPACE : owns
  ORGANIZATION ||--o{ USER : has
  WORKSPACE ||--o{ PROJECT : contains
  PROJECT ||--o{ PROPOSAL : creates
  PROPOSAL ||--o{ PROPOSAL_VERSION : versions
  PROPOSAL_VERSION ||--|| PROPOSAL_BRIEF : has
  PROPOSAL_VERSION ||--|| STRATEGY_BRIEF : has
  PROPOSAL_VERSION ||--|| STORY_PLAN : has
  STORY_PLAN ||--o{ SLIDE : contains
  SLIDE ||--o{ SLIDE_ELEMENT : contains
  PROPOSAL_VERSION ||--o{ QUALITY_REPORT : evaluated_by
  PROPOSAL_VERSION ||--o{ GENERATION_JOB : generated_by
  GENERATION_JOB ||--o{ EXPORT_ARTIFACT : outputs
  WORKSPACE ||--o{ BRAND_KIT : defines
  WORKSPACE ||--o{ KNOWLEDGE_DOCUMENT : stores
  KNOWLEDGE_DOCUMENT ||--o{ KNOWLEDGE_CHUNK : chunks
  USER ||--o{ AI_ACTION : triggers
  PROPOSAL_VERSION ||--o{ COMMENT : reviewed_by
  PROPOSAL_VERSION ||--o{ REVISION : changes
```

## Entity Notes

| Entity | Purpose | Workspace Boundary | PII/Secret |
|---|---|---|---|
| Proposal | Projectから作る提案単位 | required | 顧客情報あり |
| ProposalVersion | 編集履歴 | required | 顧客情報あり |
| ProposalBrief | Prompt Builder入力 | required | 顧客情報あり |
| StrategyBrief | Strategy出力 | required | 秘密値なし |
| StoryPlan | スライド構成 | required | 顧客情報あり |
| Slide / SlideElement | Studio編集 | required | 顧客情報あり |
| DesignTheme | テンプレート | optional shared | 秘密なし |
| BrandKit | 会社ブランド | required | ロゴ、会社情報 |
| GenerationJob | 長時間処理 | required | 入力全文保存は最小化 |
| ExportArtifact | PPTX/PDF/Beautiful.ai | required | URLは権限確認必須 |
| QualityReport | 品質結果 | required | 入力抜粋は最小化 |
| AIAction | AI操作ログ | required | prompt全文保存禁止 |
| KnowledgeDocument | ナレッジ | required | 機密情報あり得る |
| ProposalMetric | 時間/品質測定 | required | 個人識別に注意 |

## Indexes

- `(organization_id, workspace_id, project_id)`
- `(workspace_id, proposal_id, version_number)`
- `(workspace_id, created_by, created_at)`
- `(workspace_id, status, updated_at)`
- `(workspace_id, artifact_type, created_at)`

## Soft Delete

Proposal、Project、KnowledgeDocument、BrandKitはSoft Deleteを基本とする。Audit Logは削除せず保持期間で管理する。

