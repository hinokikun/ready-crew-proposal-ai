# Version 28.0 Rollback

## 方針

Version 28.0はUI/CSS/Docs中心の変更です。Backend API、DB、Migrationは変更しません。

重大なUI不具合が発生した場合は、対象commitを `git revert` で戻してください。

## 手順

1. 問題が発生したcommitを確認
2. `git revert <commit>`
3. `git push origin main`
4. GitHub Actionsを確認
5. VercelのDeploymentがReadyになることを確認
6. Renderの `/health` と `/health/ready` を確認
7. ログイン、案件入力、提出前チェック、PPTX/PDF、Beautiful.aiを再確認

## 禁止

- `git reset --hard`
- force push
- 本番DBの直接操作

## 影響範囲

- 一般利用者フローの表示
- 管理コンソールの表示
- 共通CSSトークン
- V28関連ドキュメント
