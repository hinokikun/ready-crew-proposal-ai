# RC1 Monitoring Guide

Strategy v1 RC1運用時に確認する項目。

## 主要KPI

| Item | Description | 確認頻度 |
|---|---|---|
| Engine利用率 | `strategy_v1` と `legacy` の利用比率 | 毎日 |
| Human Review率 | Review必須になった案件比率 | 毎日 |
| Quality Score平均 | Proposal Quality Reportの平均点 | 毎日 |
| Grade分布 | A/B/C/Dの分布 | 毎日 |
| Red Flag率 | Red Flagが出た案件比率 | 毎日 |
| Critical Red Flag件数 | Criticalの発生件数 | 即時 |
| Generic Fallback率 | Generic Consultingへfallbackした比率 | 毎日 |
| Compare勝敗 | LegacyとStrategy v1の比較結果 | 週次 |
| Reviewer修正量 | Human Evaluationの修正量評価 | 週次 |

## CLIで確認する項目

Benchmark:

```powershell
python -m app.strategy_engine.cli --benchmark
```

カテゴリ別:

```powershell
python -m app.strategy_engine.cli --benchmark --category vision_ocr
```

Compare:

```powershell
python -m app.strategy_engine.cli --compare ai_ocr
```

## 注意すべき兆候

- Quality Score平均が80点未満
- Critical Red Flagが1件以上
- Generic Fallback率が高い
- Human Review率が急増
- Strategy v1がLegacyに比べてScoreで劣る
- PersonaやStoryの選定が営業担当の判断とずれる
- ReviewでRejectまたはRe-evaluateが増える

## 障害時の初動

1. 新規 `strategy_v1` 利用を止める
2. `PRESENTATION_ENGINE_MODE=legacy` へ戻す
3. 対象案件のComparison Reportを確認する
4. Human Reviewコメントを確認する
5. Red FlagとQuality Category Scoreを確認する
6. 原因を記録し、再開判断までStrategy v1を使わない
