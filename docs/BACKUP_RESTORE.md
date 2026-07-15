# Backup and Restore

AI営業秘書のDBバックアップ方針です。接続文字列、APIキー、パスワードは手順書やログに貼り付けないでください。

## SQLite利用時

開発・試験導入では `app.db` をSQLite DBとして使えます。
Render無料環境のファイルシステムは永続化されない場合があります。正式運用ではRender Persistent DiskまたはPostgreSQLを検討してください。

### バックアップ

1. 可能であれば一時的に利用を止めます。
2. `backend/app.db` を日付付きファイル名でコピーします。
3. コピー後、ファイルサイズが0ではないことを確認します。
4. バックアップファイルを社内の管理場所へ保存します。

PowerShell例:

```powershell
cd backend
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item .\app.db ".\backup-app-$stamp.db"
Get-Item ".\backup-app-$stamp.db"
```

### リストア

1. 利用を止めます。
2. 現在の `app.db` を退避します。
3. バックアップファイルを `app.db` として戻します。
4. Backendを再起動します。
5. `/health` とログインを確認します。

PowerShell例:

```powershell
cd backend
Copy-Item .\app.db ".\app-before-restore.db"
Copy-Item ".\backup-app-YYYYMMDD-HHMMSS.db" .\app.db
```

## RenderでSQLiteを使う場合の注意

- 無料環境や通常の一時ディスクでは再デプロイ・再起動でDBが消える可能性があります。
- Persistent Diskを使う場合でも、定期バックアップが必要です。
- 本番運用や複数人利用ではPostgreSQLを推奨します。

## PostgreSQL利用時

Render PostgreSQL、Supabase、Neonなどへ移行できます。
`DATABASE_URL` は環境変数で管理し、ログ・README・チャットへ貼り付けないでください。

### バックアップ例

```bash
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d_%H%M%S).sql
```

### リストア例

```bash
psql "$DATABASE_URL" < backup_YYYYMMDD_HHMMSS.sql
```

大きいDBや本番環境では、Render / Supabase / Neon が提供するバックアップ機能を優先してください。

## 保存してはいけないもの

- OpenAI APIキー
- `DATABASE_URL` の全文
- ユーザーパスワード
- OAuth token / refresh token
- 案件メール本文全文
- 生成本文全文
- 顧客の機密情報

## 定期確認

- `/health` の `db_connected` が `true`
- バックアップが作成されている
- リストア手順を社内テスト環境で確認済み
- SQLite利用時は永続化リスクを関係者が理解している
## Version 18.2 Migration Backup Checklist

Before running `20260713_1820_workspace_isolation_acceptance`:

1. Back up SQLite `app.db` or take a managed PostgreSQL snapshot.
2. Record row counts:

```sql
SELECT COUNT(*) FROM quality_gates;
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM proposal_reviews;
SELECT COUNT(*) FROM proposal_knowledge;
SELECT COUNT(*) FROM analytics_events;
SELECT COUNT(*) FROM audit_logs;
```

3. Run `alembic upgrade head`.
4. Re-run the same counts.
5. Confirm the Quality Gate unique index is scoped by `(organization_id, workspace_id, project_id)`.

If counts differ unexpectedly, stop the rollout, keep Maintenance Mode enabled, and restore from the verified backup.
# Version 24.0 Backup / Restore

## SQLite利用時

1. Backendを停止、またはMaintenance Modeで新規生成を止めます。
2. `backend/app.db` を日付付きファイル名でコピーします。
3. コピー後、元DBとバックアップDBのファイルサイズを確認します。
4. 復旧時は現在の `app.db` を退避してから、バックアップファイルを `app.db` として戻します。
5. 復旧後に `/health`、`/health/ready`、ログイン、作成履歴、PPTX/PDF出力を確認します。

Render無料環境ではファイル永続化が保証されない場合があります。正式運用ではRender PostgreSQL、Supabase、NeonなどのPostgreSQL利用を推奨します。

## PostgreSQL利用時

1. Render PostgreSQL、Supabase、Neonなどの管理画面で手動バックアップまたはスナップショットを取得します。
2. 復旧前に対象環境、Database URL、バックアップ時刻を確認します。
3. 本番DBへ直接復旧する前に、検証環境へRestoreしてスキーマ整合性を確認します。
4. `alembic current` と `alembic upgrade head` の結果を確認します。
5. 復旧後にOrganization / Workspace分離、ログイン、作成履歴、Beautiful.ai履歴を確認します。

## 成果物データ

- PPTX/PDFは再生成可能なため、DBバックアップ対象は履歴、監査、設定、レビュー状態を優先します。
- Beautiful.aiの外部URLは期限切れや権限変更で開けなくなる場合があります。期限切れ時は再生成を案内してください。
