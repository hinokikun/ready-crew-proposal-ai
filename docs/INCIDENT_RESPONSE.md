# Incident Response

AI営業秘書のクラウド運用で問題が発生した時の初動手順です。

## 1. まず確認すること

- 画面に表示されたエラー文
- `request_id` が表示されていれば控える
- Vercel の Deployment 状態
- Render の Service 状態
- `/health`
- `/health/live`
- `/health/ready`
- GitHub Actions の直近結果

## 2. Backend未接続

症状:

- 画面に「Backendへ接続できません」と表示される
- `/health` が開けない

確認:

- Render service が `Live` か
- Render Logs に起動エラーがないか
- Vercel `NEXT_PUBLIC_API_URL` がRender URLを向いているか
- Backend CORSにVercel URLが含まれているか

復旧:

- Renderを再デプロイ
- 環境変数を修正
- 必要なら前回安定版へ戻す

## 3. DB接続失敗

症状:

- `/health` が `degraded`
- `db_connected` が `false`

確認:

- `DATABASE_URL` が設定されているか
- SQLiteの場合、DBファイルの保存先が利用可能か
- PostgreSQLの場合、接続先サービスが稼働しているか

復旧:

- 一時的にRenderを再起動
- SQLiteバックアップから復元
- PostgreSQL接続情報をRender環境変数で再設定

注意:

- `DATABASE_URL` の全文をログやチャットに貼らないでください。

## 4. 認証エラー

症状:

- ログインできない
- `/health` の `auth_configured` が `false`

確認:

- `APP_AUTH_SECRET`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- 初期管理者がDBに存在するか

復旧:

- Render環境変数を修正
- Backendを再起動
- 必要に応じてテスト環境で初期管理者作成を確認

## 5. OpenAI API上限

症状:

- 提案書作成時にAPI制限エラー
- 429 / quota / rate limit 系のエラー

確認:

- OpenAI API利用上限
- Render環境変数 `OPENAI_API_KEY`
- 試験導入では `USE_MOCK_AI=true` で動作確認できるか

復旧:

- 時間を置いて再実行
- 上限や支払い設定を確認
- デモ・研修ではモックモードへ切り替え

## 6. PPT/PDF生成失敗

症状:

- PPTX / PDF ダウンロードで失敗する

確認:

- `/health` の `pptx` と `pdf`
- Render Logs の同じ `request_id`
- 入力が極端に長くないか

復旧:

- 再試行
- 入力本文を短くする
- Backendを再起動

## 7. Vercel Build失敗

確認:

- `Module not found`
- 大文字小文字違いのimport
- `frontend/package-lock.json`
- `.next` キャッシュ

ローカル確認:

```powershell
cd frontend
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm.cmd ci
npm.cmd run typecheck
npm.cmd run build
```

## 8. Render起動失敗

確認:

- `backend/requirements.txt`
- Pythonバージョン
- ImportError
- `DATABASE_URL`
- `APP_AUTH_SECRET`

ローカル確認:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
```

## 9. ロールバック

- GitHubで直近の安定コミットを確認
- Vercelで過去DeploymentをPromote
- Renderで前回Deployへ戻す
- 環境変数を変更していた場合は元に戻す
- `/health/ready` と smoke test を実行

## 10. エスカレーション時に共有する情報

共有してよいもの:

- 発生日時
- 画面名
- 操作内容
- `request_id`
- `/health` の安全な結果
- Vercel / Render のエラー概要

共有してはいけないもの:

- APIキー
- パスワード
- `DATABASE_URL`
- Authorization header
- Cookie
- 案件メール本文全文
- 生成本文全文
# RC1 Incident Response

## 重大障害候補

- ログイン不能
- Backend全体停止
- DB接続不能
- 提案書作成が連続失敗
- PPT/PDF生成が連続失敗
- 権限外ユーザーが管理機能へアクセス
- 機密情報がログへ保存された可能性

## 初動

1. `MAINTENANCE_MODE=true` をRenderで設定し、新規作成を止めます。
2. `/health/live` と `/health/ready` を確認します。
3. 監査ログで直近のログイン、生成、Maintenance拒否イベントを確認します。
4. DBバックアップの有無を確認します。
5. 必要に応じてVercel/Renderの前回安定版へ戻します。

## 共有禁止

- APIキー
- `DATABASE_URL`
- `APP_AUTH_SECRET`
- Authorization token
- パスワード
- 顧客本文全文
- 生成本文全文

## 復旧判定

- `/health/ready` が `status: ok`
- admin/member/viewerでログイン確認
- 案件作成、要約PPT、詳細PPT、見積PDFのいずれかを安全なテストデータで確認
- 監査ログに復旧操作が残っている
## Version 18.2 Workspace Isolation Incident

Treat any suspected cross-organization or cross-workspace data exposure as high severity.

Immediate actions:

1. Enable Maintenance Mode.
2. Stop new proposal generation, PPT/PDF generation, and Orchestrator execution.
3. Preserve audit logs and request IDs.
4. Check affected scope:
   - user id
   - organization id
   - workspace id
   - endpoint
   - target id
5. Do not export logs that contain customer body text or generated proposal text.
6. Verify `/health/ready` and migration readiness.
7. Restore from backup if migration corrupted scope columns or Quality Gate uniqueness.

Resolution criteria:

- cross-scope API returns `403` or `404`
- admin aggregate defaults to `scope=workspace`
- system aggregate requires explicit `scope=system` and admin role
- cloud smoke test passes with forbidden workspace and other-project IDOR checks
# Version 24.0 Incident Response

## 重大障害候補

- ログイン不能
- Backend全体停止
- DB接続不能
- AI生成、PPTX、PDF、Beautiful.aiが連続失敗
- 権限外ユーザーが管理機能へアクセスできた
- Organization / Workspaceを跨いだデータ参照
- 監査ログまたはアプリログへ秘密情報が保存された疑い

## 初動

1. 新規生成を止める必要がある場合はMaintenance Modeを有効化します。
2. 発生日時、Role、Organization、Workspace、操作、`request_id`、画面幅、ブラウザを記録します。
3. Backendログ、監査ログ、Beautiful.ai診断履歴を確認します。
4. APIキー、Password、Token、顧客本文全文は障害報告へ貼り付けないでください。
5. 影響範囲を `admin`、`manager`、`member`、`viewer`、Organization、Workspace単位で切り分けます。

## 復旧後確認

1. `/health` と `/health/ready` を確認します。
2. admin/member/viewerでログイン確認します。
3. Quality Gate、要約PPTX、詳細PPTX、見積PDF、Beautiful.aiを安全なテスト案件で確認します。
4. 監査ログに復旧操作が残っていることを確認します。
5. 必要に応じてVercel Rollback、Render Manual Deploy、DB Restoreを実施します。
