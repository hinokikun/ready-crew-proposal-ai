# OPERATIONS

## Version 25.0 正式公開前運用ゲート

公開前に以下を確認してください。

1. GitHub Actions が最新 commit で成功していること。
2. Vercel が Ready で、Production Deployment が最新 commit を指していること。
3. Render が Live で、`/health` と `/health/ready` が確認できること。
4. `APP_ENV=production` が設定され、`CORS_ORIGINS` に Vercel 本番 URL のみが設定されていること。
5. API キー、Password、Token、DATABASE_URL が画面・ログ・DB に平文表示されないこと。
6. admin / manager / member / viewer の権限確認を行うこと。
7. Organization / Workspace 越境拒否を確認すること。
8. Quality Gate、要約PPTX、詳細PPTX、見積PDF、Beautiful.ai を架空案件で確認すること。

詳細は `docs/V25_0_RELEASE_GATE.md`、`docs/V25_0_PRODUCTION_UAT.md`、`docs/V25_0_RUNBOOK.md` を参照してください。

## Version 24.0 正式運用手順

### 毎日確認する項目

1. `/health` と `/health/ready` が正常であること。
2. 管理者メニューで直近のエラー、直近ログイン、Beautiful.ai診断、監査ログを確認すること。
3. 作成履歴でAI生成、PPTX、PDF、Beautiful.aiの失敗が連続していないこと。
4. Quality Gate未完了のまま外部提出されていないこと。
5. 無効化すべき退職者・異動者アカウントが残っていないこと。

### ユーザー運用

1. 新規ユーザーは管理者が作成します。
2. 通常利用者は `member`、閲覧のみは `viewer`、管理者は `admin` を指定します。
3. `manager` は既存互換とレビュー・運用補助用途として維持します。通常の新規作成UIでは選択しません。
4. 仮パスワード発行後は、次回パスワード変更必須フラグを有効化してください。
5. 削除は論理削除です。本番DBから物理削除しないでください。

### 障害時の初動

1. 画面の `request_id`、発生日時、Role、Organization、Workspace、操作内容を記録します。
2. 監査ログとBackendログで同じ `request_id` を確認します。
3. Beautiful.ai失敗時は要約PPTXまたは詳細PPTXで代替出力します。
4. DB接続異常や全体停止時はMaintenance Modeを有効化し、新規生成を止めます。
5. 復旧前にバックアップの有無を確認します。

## Version 23.1 Login Operation

1. 一般利用者には「利用者ログイン」から入るよう案内します。
2. 管理者・組織管理者には「管理者ログイン」から入るよう案内します。
3. 管理者ログインで拒否された場合は、ユーザー管理画面でロールと有効状態を確認します。
4. 利用者ログインで管理者アカウントが拒否された場合は、管理者ログインへ切り替えます。
5. パスワード忘れは管理者が一時パスワードを再設定します。
6. 既存の自動テストや旧クライアントが `login_mode` を送らない場合は、従来互換でログインできます。

## 日次運用

- `/health` でBackend、DB、AI API、PPTX、PDFの状態を確認する
- 管理者メニューで利用状況、エラー、フィードバック、監査ログを確認する
- Review / Quality Gate が未完了の案件を確認する
- 外部連携候補は承認後に案件化する

## 権限

- `admin`: 全機能、ユーザー管理、監査ログ、リリース管理、Prompt Studio
- `manager`: レビュー、リリース承認、一部管理ダッシュボード
- `member`: 通常作業、提案書作成、PPT/PDF、レビュー依頼
- `viewer`: 閲覧のみ。生成、編集、承認は不可

Backend API側でも権限を確認します。Frontendの表示制御だけに依存しません。

## 管理者メニュー分類

管理者メニューは初期状態では折りたたみ、次のカテゴリに整理します。

- 運用管理: ユーザー管理、監査ログ、リリース管理、運用準備チェック
- 改善分析: Product Analytics、Learning Dashboard、Prompt Studio、改善提案
- ナレッジ管理: Knowledge、テンプレート、承認待ち
- 外部連携: Integration、Dry Run、Connector Readiness
- 案件管理: CRM、Project Lifecycle、Review、Quality Gate
- AI実験/Prompt管理: Prompt Version、Experiment、Rollback

## 最重要動線の手動E2Eチェック

リリース前に、少なくとも次を手動確認してください。

- ログインできる
- 案件メールを貼り付けできる
- AI Workspaceが進行する
- 提案書を作成できる
- 提出前品質ゲートを確認できる
- 要約PPTをダウンロードできる
- 詳細PPTをダウンロードできる
- 見積PDFをダウンロードできる
- 上司レビューを依頼できる
- CRMに保存される
- AI通知が表示される
- 管理者メニューを閲覧できる

## エラー時の画面確認

以下の状態で、画面全体が落ちず、日本語で次の行動が表示されることを確認してください。

- Backend未接続
- 認証期限切れ
- OpenAI API上限
- PPT生成失敗
- PDF生成失敗
- 権限不足
- DB接続失敗

## バックアップ

SQLite利用時は `backend/app.db` を定期バックアップしてください。Render無料環境では永続化が保証されない場合があります。正式運用ではRender PostgreSQL、Supabase、Neonなどを推奨します。
# RC1 Operations Checklist

正式運用前に以下を確認してください。

## 毎回のリリース前

1. DBバックアップを取得する。
2. `python -m alembic upgrade head` を実行する。
3. Backendをデプロイする。
4. `/health/ready` が `status: ok` であることを確認する。
5. Frontendをデプロイする。
6. Cloud Smoke Testを実行する。
7. ログイン、案件メール貼り付け、提案書作成、要約PPT、詳細PPT、見積PDFを確認する。
8. 監査ログにログイン・生成・Maintenance操作が残ることを確認する。
9. 異常時はRollback判断を行う。

## Maintenance Mode

- 環境変数 `MAINTENANCE_MODE=true` が最優先です。
- 環境変数で有効化されている場合、画面から解除できません。
- 画面から有効化した場合も、Backendで新規生成系APIを503拒否します。

## Rate Limit運用

環境変数で調整できます。

- `RATE_LIMIT_LOGIN_LIMIT`
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS`
- `RATE_LIMIT_GENERATION_LIMIT`
- `RATE_LIMIT_GENERATION_WINDOW_SECONDS`
- `RATE_LIMIT_ADMIN_LIMIT`
- `RATE_LIMIT_ADMIN_WINDOW_SECONDS`

過剰な429が出る場合は、利用者数と操作頻度を確認してから値を調整してください。
## Version 18.2 Workspace Isolation Operation

Before production rollout with multiple organizations:

1. Enable Maintenance Mode.
2. Back up the database and verify restore.
3. Run `alembic upgrade head`.
4. Confirm `/health/ready` returns `migration_ready: true`.
5. Run `scripts/smoke_test.py` with:
   - `SMOKE_FORBIDDEN_ORGANIZATION_ID`
   - `SMOKE_FORBIDDEN_WORKSPACE_ID`
   - `SMOKE_OTHER_WORKSPACE_PROJECT_ID`
6. Confirm admin dashboards default to `scope=workspace`.
7. Confirm only system admin can use `scope=system`.
8. Confirm CSV/Markdown exports show Organization / Workspace labels.

If any cross-workspace data appears, keep Maintenance Mode enabled and treat it as a release blocker.

## Version 20.1 Proposal Optimization Operation

Before using optimization recommendations in customer-facing material:

1. Confirm the recommendation is not based on insufficient sample size.
2. Treat predicted effects as AI reference estimates, not guaranteed results.
3. Use only approved Best Practices for repeatable recommendation logic.
4. Confirm manager/admin approval before moving a recommendation into a Presentation Revision.
5. Record measured results only as aggregate metadata.
6. Do not store proposal body text, customer emails, API keys, passwords, or Beautiful.ai tokens in evidence notes.

## Version 22 Production Operations Notes

- Render / Vercel / GitHub Actions ?????????????
- DB??????????? `app.db.init_db()` ???????? `app.database.*` ??????????
- Health payload ???????????????? `app.health.build_health_payload()` ????????
- CSS? `frontend/app/styles/` ??????????`frontend/app/globals.css` ?????????????
- ?????? `docs/PRODUCTION_CHECKLIST.md` ?????Migration?Backup?Restore?Health?Beautiful.ai?Organization / Workspace????????????
# Version 22.1 Release Verification

Before promoting a build that includes Version 22.1, run:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e

cd ..\backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check

cd ..
git diff --check
```

Manual cloud checks still required:

- GitHub Actions success
- Vercel Ready
- Render Live
- Render `/health`
- Beautiful.ai status in the UI
- Manual PPTX open check
# Version 22.2 Operations Note

PPTX生成ロジックやUI Sectionを変更した場合は、通常の回帰確認に加えて以下を確認する。

- `npm.cmd run typecheck`
- `npm.cmd run check:unused`
- `npm.cmd run build`
- `npm.cmd run test:e2e`
- `.\.venv\Scripts\python.exe -m compileall app tests`
- `.\.venv\Scripts\python.exe -m pytest -q`
- `.\.venv\Scripts\python.exe -m pip check`
- `git diff --check`

PPTXの見た目確認は `docs/PPTX_VISUAL_REGRESSION.md` を参照する。LibreOffice / PowerPoint がない環境では視覚比較を成功扱いにしない。
