# Troubleshooting

開発・保守時によくある問題と確認方法。

## Feature Flag

### strategy_v1が動かない

確認:

- `PRESENTATION_ENGINE_MODE=strategy_v1` になっているか
- Review Reportが `approved` または `approved_with_changes` か
- Presentation Context生成に必要な項目が揃っているか

戻す方法:

```text
PRESENTATION_ENGINE_MODE=legacy
```

## Legacyへ戻したい

環境変数を以下にする。

```text
PRESENTATION_ENGINE_MODE=legacy
```

確認:

- 既存PPTX生成が成功する
- Strategy Engineが呼ばれない
- Presentation Contextが生成されない

## pytest

Backend全体:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

Strategy Engineのみ:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\strategy_engine -q
```

件数確認:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest --collect-only -q
```

## build

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

## CLI

Strategy Brief:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --fixture ai_ocr
```

Human Review Markdown:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --review ai_ocr
```

Quality Evaluation:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --evaluate ai_ocr
```

Benchmark:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --benchmark
```

Compare:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --compare ai_ocr
```

## Permission denied: `.pytest-tmp-*`

`git status` で以下のような警告が出る場合がある。

```text
warning: could not open directory 'backend/.pytest-tmp-.../': Permission denied
```

これは過去のpytest一時ディレクトリの権限による警告で、Git追跡対象とは限らない。

対応:

- まず `git status --short` の実際の変更一覧を確認する
- 必要なら管理者権限で一時ディレクトリを確認する
- `git clean` は安易に実行しない

## git diff --check

空白エラー確認:

```powershell
git diff --check
```

stage済み差分:

```powershell
git diff --cached --check
```

## CLIで文字化けして見える

PowerShellや端末の文字コード設定により、古いfixture文面が文字化けして見えることがある。

確認:

- JSON/Markdownの構造が壊れていないか
- テストが通っているか
- 実顧客情報が混入していないか

文字化けを理由にfixture本文を不用意に書き換えない。

## Red Flagが出る

確認:

- Evidence不足
- KPI不足
- Risk不足
- Story不整合
- Review未承認
- Next Action不足

対応:

- Human ReviewでRejectまたはRe-evaluate
- Compare ReportでLegacyとの差分確認
- Pilot Backlogへ登録

## E2Eが遅い

Playwright E2Eは全件で10分以上かかる場合がある。

対応:

- timeoutを長めに取る
- 途中timeoutした場合は再実行し、失敗とtimeoutを区別する
- テスト失敗時は対象テスト名、Console Error、画面幅を記録する
