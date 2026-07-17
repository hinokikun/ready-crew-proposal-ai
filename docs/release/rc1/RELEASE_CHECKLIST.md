# RC1 Release Checklist

ProposalPilot Strategy v1をRC1として扱う前に、以下を確認する。

## 1. Feature Flag

- [ ] `PRESENTATION_ENGINE_MODE` の現在値を確認した
- [ ] 既定値が `legacy` であることを確認した
- [ ] 無効値が指定された場合に `legacy` 扱いになることを確認した
- [ ] `strategy_v1` は明示的に有効化した場合のみ使うことを確認した

## 2. Legacyフォールバック

- [ ] `legacy` 時にStrategy Engineが呼ばれないことを確認した
- [ ] `legacy` 時にPresentation Contextが生成されないことを確認した
- [ ] 既存PPTX生成が成功することを確認した
- [ ] 不具合時に `PRESENTATION_ENGINE_MODE=legacy` へ戻せることを確認した

## 3. Human Review

- [ ] Strategy BriefのMarkdownレビューが出力できる
- [ ] `approved` のReview ReportでPresentation Contextを生成できる
- [ ] `approved_with_changes` のReview ReportでPresentation Contextを生成できる
- [ ] `reject` と `re_evaluate` はPresentation Context生成不可である

## 4. Quality Evaluator

- [ ] `python -m app.strategy_engine.cli --evaluate ai_ocr` が成功する
- [ ] JSON出力が成功する
- [ ] Red Flagが表示される
- [ ] Critical Red Flagがある場合は本番利用対象から除外する

## 5. Evaluation Harness

- [ ] `python -m app.strategy_engine.cli --benchmark` が成功する
- [ ] カテゴリ指定のBenchmarkが成功する
- [ ] Markdown / JSON / CSV出力が確認できる
- [ ] Average Score、Grade分布、Red Flag率を確認した

## 6. Comparison Framework

- [ ] `python -m app.strategy_engine.cli --compare ai_ocr` が成功する
- [ ] JSON出力が成功する
- [ ] LegacyとStrategy v1のScore差分を確認した
- [ ] Human Evaluation欄が確認できる

## 7. Tests / Build

- [ ] Backend compileall成功
- [ ] Backend pytest全件成功
- [ ] pip check成功
- [ ] Frontend typecheck成功
- [ ] Frontend build成功
- [ ] Frontend E2E成功
- [ ] git diff --check成功

## 8. Documentation

- [ ] Feature Flag手順が最新
- [ ] Operation Guideが最新
- [ ] Rollback Planが最新
- [ ] Monitoring Guideが最新
- [ ] Acceptance Criteriaが最新
- [ ] Pilot Planが最新

## 9. Git

- [ ] branchが `main`
- [ ] working treeがclean
- [ ] origin/mainとの差分を確認した
- [ ] RC1関連commitがpush済み
