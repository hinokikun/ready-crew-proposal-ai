# Version 24.0 Release Notes

## 目的

正式運用に向けて、認証、利用者管理、権限、作成履歴、監査ログ、障害対応、バックアップ復旧手順を補強しました。新しい営業AI社員や提案生成機能は追加していません。

## 主な変更

- ユーザー管理に氏名、最終ログイン、Organization、Workspace、Pilot対象、パスワード変更必須、論理削除を追加。
- 管理者によるパスワード再設定で `auth_version` を更新し、古いTokenを無効化。
- 利用者自身のパスワード変更を追加。変更後は再ログインが必要。
- 作成履歴APIを追加し、既存の `proposal_histories` をOrganization / Workspace / Roleで絞り込み。
- 監査ログに `error_type` と `http_status` を保存できるように拡張。
- Beautiful.ai生成の成功/失敗を作成履歴へ記録。
- Frontend APIに既定timeoutを追加。
- 正式運用、バックアップ、障害対応、権限表、UAT、Rollback文書を更新。

## 互換性

- 既存ログインAPI、既存ユーザー、既存DBは維持します。
- `role: "user"` は引き続き `member` として扱います。
- 既存の提案生成、PPTX、PDF、Beautiful.ai、Quality Gateの出力仕様は変更していません。

## 注意

- メール送信によるパスワードリセットは未実装です。
- 削除は論理削除です。物理削除は本番運用では実施しません。
- クラウド反映後はVercel / Renderのcommit一致を人が確認してください。
