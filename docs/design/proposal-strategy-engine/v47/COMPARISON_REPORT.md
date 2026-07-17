# Comparison Report

Comparison Reportは、同一案件に対するLegacy EngineとStrategy v1の評価結果を並べて確認するためのレポートである。

## 含める項目

| Item | Description |
|---|---|
| Total Score | Proposal Quality Reportの総合点 |
| Grade | A/B/C/D |
| Persona | 想定読者 |
| Story | 提案ストーリー |
| Presentation Pack | 使用Pack |
| KPI Pack | KPI設計 |
| Risk | リスクメッセージ |
| Red Flags | 重大な品質課題 |
| Human Review | Human Review要否と状態 |
| Improvement Points | 改善提案 |

## Markdown構成

1. Summary
2. Score比較
3. Proposal Fields比較
4. Red Flags比較
5. Improvement Points比較
6. Human Evaluation欄

## JSON構成

```json
{
  "schema_version": "proposal_comparison_report_v1",
  "fixture_name": "ai_ocr",
  "legacy": {},
  "strategy_v1": {},
  "metrics": {},
  "field_comparison": {},
  "improvement_point_comparison": {},
  "human_evaluation_template": {}
}
```

## 注意

Version47では比較用の構造を整備する。実際の顧客提出資料やDB保存には接続しない。
