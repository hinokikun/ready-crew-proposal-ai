# AI Data Contracts

## Contract Policy

- すべてのAI入出力には`schema_version`を持たせる。
- 不明な事実は`missing`, `hypothesis`, `assumption`, `needs_confirmation`で明示する。
- LLM出力は保存前にschema validationを行う。
- Version80既存の`ProposalRequest`, `ProposalAnalysis`, `PptxDownloadRequest`は互換維持する。

## Schema Summary

| Schema | Purpose | Current Relation | DB Save |
|---|---|---|---|
| ProposalBrief | Prompt Builder入力の正規化 | `ProposalRequest`を拡張 | future |
| StrategyBrief | Strategy Engine出力 | `strategy_engine.models` | future / offline |
| StoryPlan | 営業ストーリー | V80 UIのみ | future |
| SlidePlan | スライド構成 | V80 UIのみ | future |
| SlideContent | スライド本文 | `ProposalAnalysis.proposal_structure`を拡張 | future |
| VisualPlan | 図解方針 | 設計のみ | future |
| DiagramPlan | 図解構造 | `pptx_design.diagrams`へ接続予定 | future |
| LayoutPlan | レイアウト | `pptx_design.layouts`へ接続予定 | future |
| DesignTheme | PPTテンプレート | `pptx_theme.PPTX_TEMPLATE_THEMES` | future |
| BrandSettings | 会社ブランド | `PptxDownloadRequest.brand_settings` | future |
| QualityFinding | 品質指摘 | Quality Evaluator設計 | future |
| QualityReport | 品質スコア | `strategy_engine.quality`と将来統合 | future |
| GenerationJob | 非同期生成 | 未実装 | future |
| ProposalRevision | 変更履歴 | Presentation Reviewと将来統合 | future |

## ProposalBrief Fields

- `schema_version`: string, required.
- `project_name`: string, required, max 120.
- `customer_name`: string, required, max 120.
- `industry`: string, optional.
- `category`: enum, optional.
- `business_context`: string, optional, max 4000.
- `problems`: array string, required min 1.
- `goals`: array string, optional.
- `decision_maker`: string, optional.
- `budget`: string, optional.
- `deadline`: string, optional.
- `competitors`: array string.
- `constraints`: array string.
- `evidence`: array EvidenceItem.
- `assumptions`: array AssumptionItem.

## StoryPlan Fields

- `story_type`: enum.
- `main_thesis`: string, max 180.
- `audience`: object.
- `selection_reason`: string.
- `slides`: array SlidePlan.
- `missing_evidence`: array string.
- `objections`: array object.
- `next_action`: array string.
- `confidence`: number 0-1.

## QualityReport Fields

- `overall_score`: integer 0-100.
- `grade`: enum A/B/C/D.
- `findings`: array QualityFinding.
- `red_flags`: array string.
- `auto_repair_available`: boolean.
- `human_review_required`: boolean.

## Compatibility

既存APIへ渡す場合はAdapterで`ProposalBrief`から`ProposalRequest`へ変換する。既存の`ProposalRequest`を破壊的に変更しない。

