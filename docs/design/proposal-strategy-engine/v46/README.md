# Version46 Proposal Evaluation Harness

Version46では、ProposalPilotのStrategy Brief、Human Review Report、Presentation Context、Proposal Quality Reportを継続評価するためのオフライン評価基盤を追加した。

この評価基盤は本番生成フローには接続しない。PPT生成、Presentation Engine、Strategy Engineの判定ロジック、Frontend、API、DB、Migration、OpenAI、Beautiful.aiは変更しない。

## 目的

- 実案件・サンプル案件を同じ基準で評価する
- カテゴリ別に品質傾向を確認する
- `strategy_v1` と `legacy` の比較レポートを出せる構造にする
- Proposal Quality Evaluatorの結果を集計し、改善候補を見つける

## 入力

- Strategy Brief
- Human Review Report
- Presentation Context
- Proposal Quality Report

## 出力

- Evaluation Report
- Markdown
- JSON
- CSV

## CLI

```powershell
python -m app.strategy_engine.cli --benchmark
python -m app.strategy_engine.cli --benchmark --category vision_ocr
python -m app.strategy_engine.cli --benchmark --format json
python -m app.strategy_engine.cli --benchmark --category vision_ocr --format csv
```

## Version46の境界

Version46は評価基盤のみを追加する。生成ロジック、画面、API、DB、外部AI連携には接続しない。
