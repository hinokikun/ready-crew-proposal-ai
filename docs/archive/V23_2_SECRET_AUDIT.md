# Version 23.2 Secret Audit

目的: Git差分と未追跡ファイルに秘密情報が混入していないか、値を表示せずに確認します。

## 検査対象

- tracked diff: `git diff --name-only`
- untracked: `git ls-files --others --exclude-standard`

## 検査パターン

- `API_KEY`
- `SECRET`
- `PASSWORD`
- `TOKEN`
- `AUTHORIZATION`
- `DATABASE_URL`
- `OPENAI`
- `BEAUTIFUL_AI`
- `PRIVATE KEY`
- `Bearer`
- `sk-`
- `JWT`
- `Cookie`
- `Session`
- 実メールアドレスらしき文字列
- 実電話番号らしき文字列

## 結果サマリー

| 項目 | 件数/状態 |
|---|---:|
| `.env` 系ファイルのGit差分混入 | 0 |
| assignment-like hit | 46 |
| PII-like hit file | 32 |
| `BEAUTIFUL_AI...=` hit file | 13 |
| 明確な秘密値の表示 | なし |

注意:

- この監査では秘密値を表示していません。
- 変数名、テスト用値、説明文、プレースホルダーも検出対象に含まれます。
- 実値かどうか判断できないものは、人の確認必須です。

## BEAUTIFUL_AI KEY形式の確認

`BEAUTIFUL_AI...=` 形式が見つかったファイル:

| ファイル | 件数 | Git追跡 | 判定 |
|---|---:|---|---|
| `backend/alembic/versions/20260713_1900_presentation_review_loop.py` | 2 | no | migration内の列名/設定名の可能性。人の確認必須 |
| `backend/app/config.py` | 10 | yes | 設定変数名の可能性。実値がないか人の確認必須 |
| `backend/app/health.py` | 1 | no | health表示用の状態名の可能性。人の確認必須 |
| `backend/app/presentation_review.py` | 4 | no | Beautiful.ai revision連携用の識別子の可能性。人の確認必須 |
| `backend/app/routers/beautiful_ai.py` | 1 | yes | router設定名の可能性。人の確認必須 |
| `backend/app/routers/presentation_review.py` | 4 | no | router設定名の可能性。人の確認必須 |
| `backend/app/services/beautiful_ai_service.py` | 13 | yes | service設定名の可能性。人の確認必須 |
| `backend/tests/test_beautiful_ai.py` | 19 | yes | test用placeholderの可能性。人の確認必須 |
| `backend/tests/test_presentation_review.py` | 3 | no | test用placeholderの可能性。人の確認必須 |
| `docs/BEAUTIFUL_AI_INTEGRATION.md` | 12 | yes | docs内の環境変数例の可能性。人の確認必須 |
| `docs/V23_1_HANDOFF_STATUS.md` | 2 | no | 監査説明文。commit可 |
| `frontend/e2e/app.spec.ts` | 2 | yes | E2E mock/env名の可能性。人の確認必須 |
| `README.md` | 8 | yes | docs内の環境変数例の可能性。人の確認必須 |

## 人がcommit前に確認すること

1. `git diff --cached` を開く。
2. `BEAUTIFUL_AI` を検索する。
3. `=` の右側が実キーではなく、環境変数名、boolean、placeholder、mock値であることを確認する。
4. `OPENAI_API_KEY`、`DATABASE_URL`、`PASSWORD`、`TOKEN` も同様に確認する。
5. 実値があればcommitせず、先に除外または修正方針を決める。

## PII-like hitについて

メールアドレスらしき文字列は、多くがtest用の `example.com` 系アカウントの可能性があります。

電話番号らしき文字列は、migration revision ID、日付、CSS数値、docsの例が誤検出されている可能性があります。

いずれもcommit前に人が確認してください。
