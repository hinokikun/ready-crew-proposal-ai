# Comparison Metrics

Comparison Metricsは、複数案件の比較結果を集計するための指標である。

## 集計項目

| Metric | Description |
|---|---|
| Legacy勝利件数 | LegacyのScoreが高い件数 |
| Strategy勝利件数 | Strategy v1のScoreが高い件数 |
| 同点件数 | Scoreが同点の件数 |
| 平均差分 | Strategy v1 Score - Legacy Scoreの平均 |
| Red Flag改善率 | Strategy v1でRed Flagが減った比率 |
| Human Review改善率 | Strategy v1でHuman Review要否が改善した比率 |

## 勝敗判定

- Scoreが高い方を勝ちとする
- 同点の場合は `tie`
- Grade、Red Flag、Human Reviewは補助指標として扱う

## Red Flag改善率

Strategy v1のRed Flag件数がLegacyより少ない場合を改善とする。

## Human Review改善率

Strategy v1でHuman Reviewが不要になり、Legacyでは必要だった場合を改善とする。

## 注意

Version47の比較指標は営業レビューの判断材料であり、自動的に本番Engineを切り替えるものではない。
