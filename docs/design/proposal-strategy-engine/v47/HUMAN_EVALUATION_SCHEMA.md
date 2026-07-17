# Human Evaluation Schema

Human Evaluationは、営業担当が比較レポートを読んで手動評価するための入力欄である。

Version47ではDB保存しない。MarkdownまたはJSONの仕様だけを定義する。

## 評価項目

| Field | Range | Description |
|---|---|---|
| `ease_of_understanding` | 1〜5 | 理解しやすさ |
| `persuasiveness` | 1〜5 | 説得力 |
| `sales_readiness` | 1〜5 | 営業で使えるか |
| `revision_effort` | 1〜5 | 修正量 |
| `free_comment` | text | 自由コメント |

## JSON例

```json
{
  "ease_of_understanding": {
    "label": "理解しやすさ",
    "score_range": "1-5",
    "value": null,
    "note": ""
  },
  "persuasiveness": {
    "label": "説得力",
    "score_range": "1-5",
    "value": null,
    "note": ""
  },
  "sales_readiness": {
    "label": "営業で使えるか",
    "score_range": "1-5",
    "value": null,
    "note": ""
  },
  "revision_effort": {
    "label": "修正量",
    "score_range": "1-5",
    "value": null,
    "note": ""
  },
  "free_comment": ""
}
```

## 運用ルール

- 実顧客情報、個人情報、秘密情報はコメントに書かない
- 評価は人間の判断を優先する
- 平均点が低い項目はVersion48以降の改善候補にする
