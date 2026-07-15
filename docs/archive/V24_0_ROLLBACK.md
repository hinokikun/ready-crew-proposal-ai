# Version 24.0 Rollback

## 原則

Rollbackは `git reset` ではなく、GitHub上で対象commitを確認して `git revert` を使います。本番DBは自動削除しません。

## 手順

1. GitHubでVersion 24.0のcommitを確認します。
2. 直前の安定commitを確認します。
3. 必要ならVercelの過去DeploymentをPromoteします。
4. Renderで直前のManual Deployを選択します。
5. DB変更は非破壊列追加のため、通常はDB downgradeを行いません。
6. 重大障害時はMaintenance Modeを有効化して新規生成を止めます。
7. 復旧後に `/health`、`/health/ready`、admin/member/viewerログイン、Quality Gate、PPTX/PDF、Beautiful.aiを確認します。

## DB注意点

Version 24.0で追加される列は以下です。

- `users.display_name`
- `users.last_login_at`
- `users.password_change_required`
- `users.deleted_at`
- `audit_logs.error_type`
- `audit_logs.http_status`

これらは既存データを消さない追加列です。Rollback時も保持して問題ありません。

## 障害報告に必要な情報

- 発生日時
- Role
- Organization / Workspace
- 操作手順
- request_id
- error_type
- Frontend / Backend commit
- Render / Vercel deploy status

APIキー、Password、Token、顧客本文全文は記載しないでください。
