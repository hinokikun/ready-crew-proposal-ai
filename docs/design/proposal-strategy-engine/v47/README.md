# Version47 Real Proposal Comparison Framework

Version47では、同一案件について `legacy` と `strategy_v1` の品質評価結果を比較するオフライン比較基盤を追加した。

この比較基盤は本番生成フローには接続しない。PPT生成、Presentation Engine、Strategy Engineの判定ロジック、Frontend、API、DB、Migration、OpenAI、Beautiful.aiは変更しない。

## 目的

- 同一案件でLegacy EngineとStrategy v1の評価結果を並べる
- 営業担当がMarkdownで比較レビューできるようにする
- Proposal Quality ReportとHuman Review Reportの差分を確認する
- 改善ポイントを比較し、Version48以降の改善判断に使う

## CLI

```powershell
python -m app.strategy_engine.cli --compare ai_ocr
python -m app.strategy_engine.cli --compare crm
python -m app.strategy_engine.cli --compare ai_ocr --format json
```

## 出力

- Markdown
- JSON

## Version47の境界

Version47は比較評価基盤のみであり、PPT生成結果や本番画面には影響しない。
