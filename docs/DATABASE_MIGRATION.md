# Database Migration Guide

対象: v1.0 RC1  
目的: SQLiteを維持しながら、PostgreSQL/Alembicへ移行できる状態を作る。

## 基本方針

- 既存SQLiteの `app.db` は自動削除しません。
- `DATABASE_URL` の全文はログ、画面、Issue、チャットへ貼り付けません。
- 正式運用ではAlembic Migrationを利用します。
- 開発・テストでは後方互換のため、起動時スキーマ作成を利用できます。
- 本番では `ALLOW_STARTUP_SCHEMA_MIGRATION=false` を推奨します。

## 既存SQLite環境

1. Backendを停止します。
2. DBをバックアップします。

```powershell
cd backend
New-Item -ItemType Directory -Force backup
Copy-Item .\app.db .\backup\app_yyyyMMdd_HHmm.db
```

3. 依存関係を更新します。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Migrationを確認します。

```powershell
$env:DATABASE_URL="sqlite:///app.db"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

既存DBへ初回baselineを適用する場合は、事前バックアップを必須にしてください。

## 新規PostgreSQL環境

1. Render PostgreSQL、Supabase、NeonなどでDBを作成します。
2. Render Secretsに `DATABASE_URL` を設定します。
3. Release Commandまたは手動でMigrationを実行します。

```powershell
cd backend
$env:DATABASE_URL="postgresql://..."
.\.venv\Scripts\python.exe -m alembic upgrade head
```

4. `/health/ready` を確認します。

## Render設定例

Backend起動前に以下を設定してください。

- `DATABASE_URL`
- `APP_AUTH_SECRET`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `OPENAI_API_KEY` または `USE_MOCK_AI=true`
- `ALLOW_STARTUP_SCHEMA_MIGRATION=false`

Release Command例:

```bash
cd backend && python -m alembic upgrade head
```

## Migration確認

空SQLite DBで確認する例:

```powershell
cd backend
$env:DATABASE_URL="sqlite:///migration-test.db"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

確認項目:

- `users`
- `projects`
- `quality_gates`
- `alembic_version`

## ロールバック方針

RC1 baselineの `downgrade` はデータ損失を避けるため意図的に無効化しています。

問題が起きた場合:

1. 新規トラフィックをMaintenance Modeで停止
2. 直前バックアップから復旧
3. Vercel/Renderの前回安定版へ戻す
4. `/health/ready` と主要操作を確認

## 失敗時の復旧

- Migration失敗時は `ALLOW_STARTUP_SCHEMA_MIGRATION=false` の本番では `/health/ready` がdegradedになります。
- SQLiteではバックアップDBへ差し替えます。
- PostgreSQLではプロバイダーのバックアップ復元、または `pg_restore` を利用します。
- 復旧時も `DATABASE_URL` の全文は共有しません。
