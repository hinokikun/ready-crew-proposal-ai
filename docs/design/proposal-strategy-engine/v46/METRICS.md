# Evaluation Metrics

Evaluation Harnessでは、Proposal Quality Reportを横断集計し、カテゴリ別・エンジン別の品質傾向を確認する。

## 集計指標

| Metric | Description |
|---|---|
| Average Score | 100点満点の平均点 |
| Grade Distribution | A/B/C/Dの分布 |
| Red Flag Count | Red Flagの合計件数 |
| Human Review Rate | Human Reviewが必要なケース比率 |
| Generic Fallback Rate | Genericへfallbackしたケース比率 |
| Confidence Distribution | high / medium / lowの分布 |
| Persona Distribution | Personaの分布 |
| Story Distribution | Storyの分布 |
| Pack Usage | Presentation Packの利用率 |

## Confidence Bucket

| Bucket | Range |
|---|---|
| high | 0.80以上 |
| medium | 0.60以上0.80未満 |
| low | 0.60未満 |

## Red Flag

Red FlagはProposal Quality Evaluatorの検出結果を集計する。

代表例:

- `evidence_insufficient`
- `kpi_missing`
- `risk_missing`
- `story_inconsistent`
- `review_not_approved`
- `cta_missing`

## Improvement Candidates

Red Flagの発生件数が多い順に、改善候補として一覧化する。

Version46では自動修正は行わない。改善候補はVersion47以降の分析対象とする。
