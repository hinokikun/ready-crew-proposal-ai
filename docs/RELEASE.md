# RELEASE

## リリース前チェック

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
```

```powershell
cd backend
python -m compileall app tests
.\test_backend.ps1
```

リポジトリ直下:

```powershell
git diff --check
```

## GitHub Actions

`.github/workflows/test.yml` は次を実行します。

- Backend: Python 3.13、依存インストール、`python -m compileall app tests`、`python -m pytest`
- Frontend: Node.js 24、`npm ci`、`npm run build`
- Lint/Syntax: `git diff --check`、TypeScript型チェック、未使用importチェック

`pytest` が失敗した場合、Actionsは失敗扱いになります。

## Vercel確認

- Root Directory が `frontend` になっている
- `NEXT_PUBLIC_API_URL` がRender Backend URLを指している
- Module not found が出た場合はimport先ファイルの存在と大文字小文字を確認する
- `.next` キャッシュ破損が疑われる場合はローカルで削除して再ビルドする

```powershell
cd frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm.cmd run build
```

## Render確認

- `render.yaml` がリポジトリ直下にある
- `backend/requirements.txt` がPython 3.13でインストールできる
- `/health` が正常に返る
- `APP_AUTH_SECRET`、`INITIAL_ADMIN_EMAIL`、`INITIAL_ADMIN_PASSWORD`、`OPENAI_API_KEY`、`DATABASE_URL` をSecretsへ設定する

## 手動E2Eチェック

本番反映前に以下を確認してください。

- ログイン
- 案件メール貼り付け
- AI Workspace進行
- 提案書作成
- 提出前品質ゲート
- 要約PPTダウンロード
- 詳細PPTダウンロード
- 見積PDFダウンロード
- 上司レビュー依頼
- CRM保存
- 通知表示
- 管理者メニュー閲覧

## ロールバック手順

- GitHubで前回の安定コミットを確認する
- Vercelで過去DeploymentをPromoteする
- Renderで前回Deployを確認する
- 環境変数を変更した場合は元に戻す
- DB変更がある場合はバックアップから復元できるか確認する

## Prompt Rollback

Prompt Studioで過去Versionを選択し、「戻す」を実行します。実行時は監査ログへ記録されます。
# v1.0 RC1 Release Procedure

正式版RC1では、以下を順番に実施します。

1. DBバックアップ
   - SQLite: `Copy-Item backend\app.db backend\backup\app_yyyyMMdd_HHmm.db`
   - PostgreSQL: provider backupまたは `pg_dump`
2. Migration
   - `cd backend`
   - `python -m alembic upgrade head`
3. Backend deploy
   - Renderへデプロイ
   - `APP_AUTH_SECRET`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD`, `DATABASE_URL`, `OPENAI_API_KEY` を確認
4. `/health/ready`
   - `status: ok`
   - `auth_configured: true`
   - `db_connected: true`
   - `db_tables_count > 0`
5. Frontend deploy
   - Vercel環境変数 `NEXT_PUBLIC_API_URL` を確認
6. Smoke Test
   - ログイン
   - 案件メール貼り付け
   - 提案書作成
   - 要約PPT/詳細PPT/見積PDF
7. 主要操作確認
   - admin/member/viewerの権限
   - Maintenance Mode
   - Quality Gate
   - Review
8. 監査ログ確認
   - ログイン
   - 生成
   - Maintenance開始/解除/拒否
9. ロールバック判断
   - Vercelの前回DeploymentをPromote
   - Renderの前回Deployを確認
   - DBはバックアップから復旧

本番CORSは正式なVercel URLまたは独自ドメインへ限定してください。

## Version 22 Release Readiness Addendum

Version 22?????????????????????API??DB??????????????

????:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e

cd ..\backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check

cd ..
git diff --check
```

Production??:

- Vercel Ready
- Render Live
- `/health/ready` ? `status: ok` ???????? degraded ?????
- Beautiful.ai status ???Backend??????
- Organization / Workspace?????Workspace????????
- Backup / Restore ?????????????
# Version 24.0 Release Procedure

1. 変更ファイルに秘密情報が含まれていないことを確認します。
2. Backend: `compileall`、全pytest、`pip check` を実行します。
3. Frontend: `typecheck`、`check:unused`、`build`、E2Eを実行します。
4. `git diff --check` を確認します。
5. Migration `20260715_2400` が非破壊列追加のみであることを確認します。
6. commit後、GitHub Actionsが最新commitで成功していることを確認します。
7. Vercel ProductionがReadyで、commitがGitHub最新commitと一致することを確認します。
8. RenderがLiveで、`/health` と `/health/ready` が正常であることを確認します。
9. `docs/V24_0_UAT.md` に沿ってブラウザ確認を実施します。
10. 問題があれば `docs/V24_0_ROLLBACK.md` に沿ってRollback判断を行います。
