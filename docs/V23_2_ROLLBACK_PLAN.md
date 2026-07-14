# Version 23.2 Rollback Plan

目的: Version 23.0 UI反映後に重大不具合が出た場合の安全な戻し方を整理します。

## 基本方針

- 原則として `git revert` を使います。
- `git reset --hard` は共有branchでは使わないでください。
- 本番DBに影響するmigrationがある場合は、DB rollback方針を確認してから戻します。

## 前commitを確認する方法

```bat
git log --oneline -10
```

GitHub上でも、commit履歴から前回安定版のcommitを確認できます。

## revert と reset の違い

### revert

- 変更を打ち消す新しいcommitを作ります。
- 履歴が残ります。
- 共有branchで安全です。

例:

```bat
git revert <commit_hash>
```

### reset

- 履歴そのものを戻します。
- 共有branchでは危険です。
- 今回のrollbackでは原則使いません。

## Vercel Instant Rollback

Vercel Dashboardで過去のProduction Deploymentを選び、PromoteまたはRollbackします。

確認:

- rollback先のcommit
- Production URLの表示
- FrontendとBackendのcommit不一致が起きていないか

## Render Manual Deploy

Render Dashboardで過去commitを指定してManual Deployする方法を確認します。

確認:

- 対象commit
- 環境変数
- 起動ログ
- `/health`
- `/health/ready`

## DB Migrationがある場合の注意

Version 23.0 Simple Guided UI自体はDB変更なしです。

ただし、作業ツリーにはVersion 18〜20のmigration候補があります。

注意:

- migrationを本番適用済みの場合、UIだけrollbackしてもDB状態は戻りません。
- rollback前に適用済みmigrationを確認してください。
- DB backupを取得してから対応してください。

## Version 23.0 rollback対象

主に以下:

- `frontend/components/guided-flow/`
- `frontend/app/styles/guided-flow.css`
- `frontend/components/AppShell.tsx`
- `frontend/components/Header.tsx`
- `frontend/e2e/app.spec.ts`
- `docs/SIMPLE_UI_SPEC.md`
- `docs/GUIDED_FLOW.md`
- `docs/QUALITY_GATE_UI.md`
- `docs/BEAUTIFUL_AI_USER_FLOW.md`

## rollback後のHealth確認

```text
https://ready-crew-proposal-ai.onrender.com/health
https://ready-crew-proposal-ai.onrender.com/health/ready
```

確認:

- BackendがLive
- DB接続正常
- migration ready
- maintenance modeが意図どおり

## rollback後のUAT項目

- ログイン
- 案件入力
- AI生成
- Quality Gate
- 要約PPTX
- 詳細PPTX
- PDF
- Beautiful.ai
- admin/member/viewer権限
- Workspace分離

## 障害時の記録

`docs/V23_1_BUG_REPORT_TEMPLATE.md` に沿って記録します。

秘密情報、顧客本文全文、APIキー、Password、Tokenは記載しないでください。
