# Operations FAQ

## ログインできない

- ログイン入口が利用者用か管理者用か確認する。
- メールアドレスとPasswordを確認する。
- inactive userではないか確認する。
- rate limitの場合は時間を置いて再試行する。
- admin作成直後はRoleとOrganization / Workspaceを確認する。

## Exportできない

- `PROPOSAL_EXPORT_ENABLED=true`か確認する。
- adminでログインしているか確認する。
- Proposal Previewが生成済みか確認する。
- Human Reviewが`Export可能`になっているか確認する。
- `needs_revision`または`regenerate_recommended`の場合はExport不可。

## Feature FlagがOFF

- Backend側の環境変数を確認する。
- Frontend側の公開環境変数は表示補助であり、Backendが最終判定。
- Render / Vercelでは環境変数変更後に再デプロイが必要な場合がある。

## PPTXが取得できない

- Export成功後に`PowerPointをダウンロード`が表示されているか確認する。
- Networkで`/api/sales-assistant/export/download`のstatusを確認する。
- 401/403は認証・権限、409はHuman Review、500はBackendログを確認する。
- ファイルが0 byteの場合はNo-Go候補として記録する。

## Beautiful.aiが使えない

- `BEAUTIFUL_AI_ENABLED`
- `BEAUTIFUL_AI_API_KEY`
- `BEAUTIFUL_AI_API_MODE`
- `BEAUTIFUL_AI_BASE_URL`
- 管理画面のBeautiful.ai診断
- Rate LimitまたはWorkspace/Theme設定

## 管理者権限がない

- admin以外にはAI Sales Assistant管理画面、User Management、診断、UATなどを表示しない。
- manager/member/viewerで管理APIが403になることは正常。

## Proposal Previewが生成できない

- `SALES_ASSISTANT_PROPOSAL_ENABLED=true`か確認する。
- Sales Assistant Briefが生成済みか確認する。
- Backendログの`sales_assistant_proposal_generation_error`を確認する。
- Sales Assistant結果は保持されるため、Proposalだけ再生成する。

## Pilotを止めたい

- まずFeature Flagで対象機能をOFFにする。
- Criticalの場合は`rollback_checklist.md`に従う。
- issue_backlogへ原因と暫定対応を記録する。
