# Roles and Permissions

## Current Roles

現在の主要Roleは `admin`, `manager`, `member`, `viewer` である。互換上 `user` は `member` として扱う方針が既存コードにある。

| Role | 現在実装されている範囲 | 将来必要な範囲 |
|---|---|---|
| admin | 管理画面、ユーザー管理、監査、診断、UAT、Organization/Workspace管理 | system administrator相当の分離、秘密設定の閲覧禁止/更新権限分離 |
| manager | 分析、案件、履歴の広い閲覧 | チーム配下のProposal Studioレビュー、承認、品質管理 |
| member | 案件入力、提案生成、PPTX/PDF/Beautiful.ai、履歴 | 自分または所属WorkspaceのProposal編集、AIレビュー依頼 |
| viewer | 閲覧中心 | 出力不可、編集不可、コメント可否を明確化 |

## Permission Matrix

| 機能 | member | manager | admin | system administrator候補 |
|---|---:|---:|---:|---:|
| ログイン | 可 | 可 | 可 | 可 |
| 案件作成 | 可 | 可 | 可 | 原則不可 |
| Proposal生成 | 可 | 可 | 可 | 原則不可 |
| Proposal Studio編集 | 将来可 | 将来可 | 将来可 | 不可 |
| PPTX / PDF出力 | 可 | 可 | 可 | 原則不可 |
| Beautiful.ai出力 | 可 | 可 | 可 | 原則不可 |
| 作成履歴閲覧 | 自分/Workspace | 権限範囲 | 全体 | 監査目的のみ |
| 業務改善レポート | 自分 | チーム | 全体 | 運用監査 |
| ユーザー管理 | 不可 | 不可 | 可 | 可 |
| 監査ログ | 不可 | 限定 | 可 | 可 |
| Secret診断 | 不可 | 不可 | 値なしで可 | 値なしで可 |
| Feature Flag変更 | 不可 | 不可 | 将来可 | 可 |

## Data Boundaries

- Organization境界: すべての業務データの最上位境界。
- Workspace境界: 案件、提案、履歴、Knowledge、改善レポートの実務境界。
- Object Level Authorization: Proposal、Project、ExportArtifact、QualityReportごとに必要。

## Create / Edit / Delete

| Role | 作成 | 編集 | 削除 |
|---|---|---|---|
| member | Project, Proposal, Report | 自分/Workspace内 | 原則Soft Delete依頼 |
| manager | Project, Proposal, Report | チーム範囲 | 論理削除依頼 |
| admin | User, Workspace, 設定 | 管理範囲 | 最後のadmin保護付き |
| system administrator | 環境、運用設定 | システム設定 | DB直接削除不可 |

## Current Gaps

- Proposal Studio単位の編集権限は未定義。
- ExportArtifact URLの細かな有効期限・署名URLは将来設計。
- managerの範囲定義が組織・Workspace・チームのどれか曖昧。
- system administrator相当は現在Roleとして未実装。

