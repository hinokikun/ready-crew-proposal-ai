# Version 23.1 GitHub Actions Guide

目的: GitHub Actions の結果を、人間が最新 commit と照合しながら確認する手順です。

## 確認する Workflow

確認対象:

- Backend pytest
- Frontend build
- Lint and syntax checks
- Frontend Playwright E2E
- Cloud deployment smoke test

## 状態の見方

- 緑: 成功
- 黄: 実行中
- 赤: 失敗
- 灰色: skip または未実行

注意:

- 古い赤い履歴と、最新 commit の赤い失敗を混同しないでください。
- 必ず最新 commit hash と workflow run の commit hash を照合してください。

## 最新 commit と Workflow Run の照合

1. GitHub のリポジトリを開きます。
2. `Code` タブで最新 commit hash を確認します。
3. `Actions` タブを開きます。
4. 一番上の workflow run を開きます。
5. workflow run に表示される commit hash が最新 commit と一致していることを確認します。

一致しない場合:

- GitHub Actions がまだ開始していない可能性があります。
- push した branch が `main` ではない可能性があります。
- 古い run を見ている可能性があります。

## Backend pytest

期待結果:

- Python setup が成功
- `pip install -r requirements.txt` が成功
- `pytest` が成功

失敗時に見る場所:

- Python version
- 依存インストールログ
- 失敗した test 名
- DB 初期化エラー
- 権限テストの失敗

## Frontend build

期待結果:

- Node.js setup が成功
- `npm ci` が成功
- `npm run build` が成功

失敗時に見る場所:

- `Module not found`
- TypeScript error
- ESLint / unused import
- Vercel とローカルの Node version 差

## Lint and syntax checks

期待結果:

- `git diff --check` 相当が成功
- TypeScript 型チェックが成功
- Python 構文チェックが成功

失敗時に見る場所:

- trailing whitespace
- import path の大文字小文字違い
- Python compile error
- 未使用 import

## Frontend Playwright E2E

期待結果:

- ログイン画面表示
- Dashboard 表示
- Guided Flow 表示
- Quality Gate UI
- Beautiful.ai disabled 理由表示
- 権限別メニュー表示
- モバイル表示

失敗時に見る場所:

- E2E screenshot
- trace
- test 名
- selector が変わっていないか
- dev server 起動失敗

## Cloud deployment smoke test

期待結果:

- Render `/health` が正常
- Render `/health/ready` が正常
- Vercel の Frontend が Ready
- Beautiful.ai route が登録されている

失敗時に見る場所:

- Render deploy logs
- Vercel build logs
- 環境変数
- Frontend と Backend の commit 不一致
