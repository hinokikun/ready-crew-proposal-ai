# Benchmark

Benchmarkは、評価データセットを一括実行し、Proposal Quality ReportをEvaluation Reportへ集計するCLIである。

## 実行例

全カテゴリ:

```powershell
python -m app.strategy_engine.cli --benchmark
```

カテゴリ指定:

```powershell
python -m app.strategy_engine.cli --benchmark --category vision_ocr
```

JSON出力:

```powershell
python -m app.strategy_engine.cli --benchmark --format json
```

CSV出力:

```powershell
python -m app.strategy_engine.cli --benchmark --category vision_ocr --format csv
```

## 比較対象

| Engine Mode | Description |
|---|---|
| `strategy_v1` | Strategy Brief、Human Review、Presentation Contextを通した評価 |
| `legacy` | 既存フローとの比較用モード |

Version46では、本番Legacy生成ロジックには接続しない。比較可能なレポート構造を提供する。

## 運用ルール

- BenchmarkはローカルまたはCIで実行する
- 実顧客データは使わない
- 出力結果に秘密情報を含めない
- 品質低下を検出した場合、生成ロジックへ直接接続せず原因を分析する
