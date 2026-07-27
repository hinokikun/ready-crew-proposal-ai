# SCR-180 Admin

## Purpose

ユーザー、権限、監査、診断、UAT、運用状態を管理する。

## Components

- AdminUsersPanel
- AdminAuditLogPanel
- SystemDiagnosticsPanel
- BeautifulAiStatusCard / diagnostics
- AdminOperationReadinessPanel
- AdminPilotDashboardPanel

## States

- 403: 管理者権限が必要。
- Empty: まだログやユーザーがない。
- Error: request_idと次の対応を表示。

## Future

system administrator相当を分離し、秘密設定やFeature Flag更新権限をadminからさらに分ける。

