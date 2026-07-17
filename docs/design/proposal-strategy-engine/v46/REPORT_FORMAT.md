# Evaluation Report Format

Evaluation ReportはMarkdown、JSON、CSVで出力できる。

## Markdown

人間が読むレビュー用。以下を含む。

- Summary
- Category Summary
- Legacy Comparison
- Red Flags
- Improvement Candidates
- Case Results

## JSON

自動集計・CI保存用。主な構造は以下。

```json
{
  "schema_version": "proposal_evaluation_report_v1",
  "dataset_version": "evaluation_dataset_v1",
  "category_filter": null,
  "summary": {},
  "category_summaries": [],
  "red_flag_summary": {},
  "improvement_candidates": [],
  "legacy_comparison": {},
  "results": []
}
```

## CSV

表計算ソフトで確認するためのケース別一覧。

列:

- `case_id`
- `category`
- `category_label`
- `fixture_name`
- `title`
- `engine_mode`
- `total_score`
- `grade`
- `red_flag_count`
- `red_flags`
- `human_review_required`
- `confidence`
- `persona`
- `story`
- `pack`
- `generic_fallback`

## 保存方針

Benchmark出力は必要に応じてCI artifactsやローカルファイルへ保存する。Version46ではDB保存しない。
