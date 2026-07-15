# Version 23.2 Safe Commit Plan

目的: 現在の未コミット変更を、途中で壊れにくいcommit単位へ分ける案です。

重要:

- この計画は提案です。
- 実際の `git add`、`git commit`、`git push` は行っていません。
- 各commit前に `git diff --cached` で秘密情報と意図しないファイルを確認してください。

## Commit 1: Add Organization and Workspace isolation foundation

目的:

- Organization / Workspace分離のBackend基盤とFrontend切替をまとめます。

含めるファイル:

- `backend/alembic/versions/20260713_1820_workspace_isolation_acceptance.py`
- `backend/app/context.py`
- `backend/app/dependencies/`
- `backend/app/organization.py`
- `backend/app/routers/organizations.py`
- `backend/app/scope_policy.py`
- `backend/app/scoping/`
- `backend/app/role_permissions.py`
- `backend/tests/test_organizations.py`
- `backend/tests/test_workspace_acceptance.py`
- `frontend/client-api/organizations.ts`
- `frontend/components/WorkspaceSwitcher.tsx`
- `frontend/lib/roles.ts`
- `docs/ORGANIZATION.md`
- `docs/WORKSPACE.md`
- `docs/ORGANIZATION_MIGRATION.md`
- `docs/WORKSPACE_ACCEPTANCE_PLAN.md`
- `docs/WORKSPACE_API_AUDIT.md`
- `docs/WORKSPACE_ISOLATION_AUDIT.md`

除外:

- Presentation Review
- Proposal Optimization
- Guided Flow

先に必要なcommit:

- なし

commit後に実行するテスト:

- Backend compileall
- pytest
- Frontend typecheck
- Frontend build

想定リスク:

- 既存データのscope付与
- Workspace越境制御

rollback:

- 原則 `git revert <commit>` を使用します。

## Commit 2: Add Presentation Review and Revision workflow

目的:

- Presentation Review / Revision / Beautiful.ai revision連携をまとめます。

含めるファイル:

- `backend/alembic/versions/20260713_1900_presentation_review_loop.py`
- `backend/alembic/versions/20260713_1910_presentation_review_acceptance.py`
- `backend/app/presentation_review.py`
- `backend/app/routers/presentation_review.py`
- `backend/tests/test_presentation_review.py`
- `frontend/client-api/presentationReview.ts`
- `frontend/components/PresentationReviewPanel.tsx`
- `docs/PRESENTATION_REVIEW.md`
- `docs/PRESENTATION_REVIEW_ACCEPTANCE.md`
- `docs/PRESENTATION_REVISION.md`

先に必要なcommit:

- Commit 1

commit後に実行するテスト:

- pytest
- Frontend build
- Playwright E2E

想定リスク:

- Beautiful.ai revision状態の表示
- Workspace分離との組み合わせ

rollback:

- `git revert <commit>`

## Commit 3: Add Proposal Optimization workflow

目的:

- Proposal Optimization / Backlog / Best Practiceをまとめます。

含めるファイル:

- `backend/alembic/versions/20260713_2000_proposal_optimization.py`
- `backend/alembic/versions/20260713_2010_proposal_optimization_acceptance.py`
- `backend/app/proposal_optimization.py`
- `backend/app/routers/proposal_optimization.py`
- `backend/tests/test_proposal_optimization.py`
- `frontend/client-api/proposalOptimization.ts`
- `frontend/components/ProposalOptimizationPanel.tsx`
- `docs/PROPOSAL_OPTIMIZATION.md`
- `docs/PROPOSAL_OPTIMIZATION_ACCEPTANCE.md`
- `docs/BEST_PRACTICES.md`
- `docs/IMPROVEMENT_BACKLOG.md`

先に必要なcommit:

- Commit 1
- Commit 2

commit後に実行するテスト:

- pytest
- Frontend build
- Playwright E2E

想定リスク:

- 推奨改善の権限制御
- Presentation Reviewとの連携

rollback:

- `git revert <commit>`

## Commit 4: Harden Beautiful.ai production verification

目的:

- Beautiful.ai status、mock、enabled、route確認を安定化します。

含めるファイル:

- `backend/app/config.py`
- `backend/app/routers/beautiful_ai.py`
- `backend/app/services/beautiful_ai_service.py`
- `backend/tests/test_beautiful_ai.py`
- `docs/BEAUTIFUL_AI_INTEGRATION.md`
- `docs/BEAUTIFUL_AI_USER_FLOW.md`
- 関連する `README.md` 差分

先に必要なcommit:

- Commit 1

commit後に実行するテスト:

- pytest
- Frontend build
- Playwright E2E

想定リスク:

- 環境変数名と実値の混同
- Mock/Enabled判定

rollback:

- `git revert <commit>`

## Commit 5: Split backend and frontend architecture

目的:

- 巨大ファイル分割、repository分割、PPTX service分割、CSS分割、AppShell分割をまとめます。

含めるファイル:

- `backend/app/database/`
- `backend/app/db.py`
- `backend/app/repository_parts/`
- `backend/app/repositories.py`
- `backend/app/router_registry.py`
- `backend/app/services/pptx_parts/`
- `backend/app/services/pptx_theme.py`
- `backend/app/services/pptx_service.py`
- `frontend/app/globals.css`
- `frontend/app/styles/`
- `frontend/components/app-shell/`
- `frontend/components/AppShell.tsx`
- `backend/tests/test_pptx_structure_regression.py`
- `backend/tests/snapshots/`
- `scripts/compare_pptx_previews.py`
- `scripts/render_pptx_preview.py`
- architecture/refactoring docs

先に必要なcommit:

- Commit 1

commit後に実行するテスト:

- Frontend typecheck
- Frontend build
- Frontend E2E
- Backend compileall
- pytest
- pip check

想定リスク:

- import漏れ
- CSS import漏れ
- snapshotの意図しない変化

rollback:

- `git revert <commit>`

## Commit 6: Add Simple Guided Proposal Workflow

目的:

- Version 23.0 Simple Guided UIをまとめます。

含めるファイル:

- `frontend/components/guided-flow/`
- `frontend/app/styles/guided-flow.css`
- `frontend/components/AppShell.tsx`
- `frontend/components/Header.tsx`
- `frontend/e2e/app.spec.ts`
- `docs/SIMPLE_UI_SPEC.md`
- `docs/GUIDED_FLOW.md`
- `docs/QUALITY_GATE_UI.md`
- `docs/UAT_CHECKLIST.md`
- `README.md`

先に必要なcommit:

- Commit 5

commit後に実行するテスト:

- Frontend typecheck
- Frontend check:unused
- Frontend build
- Frontend E2E

想定リスク:

- Quality Gate完了表示
- Beautiful.ai disabled理由
- member/admin表示差分

rollback:

- `git revert <commit>`

## Commit 7: Add test and smoke verification updates

目的:

- E2E、backend tests、smoke testを整理します。

含めるファイル:

- `frontend/e2e/app.spec.ts`
- `backend/tests/*.py`
- `scripts/smoke_test.py`
- `docs/TESTING.md`
- `docs/DEPLOYMENT_VERIFICATION.md`

先に必要なcommit:

- Commit 1〜6

commit後に実行するテスト:

- すべて

想定リスク:

- E2EがUI変更に依存
- smoke testに実URLや秘密値が混ざらないこと

rollback:

- `git revert <commit>`

## Commit 8: Add handoff, UAT, and manuals

目的:

- Version 23.1 / 23.2 の引き継ぎ、UAT、マニュアル資料をまとめます。

含めるファイル:

- `docs/V23_1_*.md`
- `docs/V23_2_*.md`
- `docs/USER_MANUAL_TEXT.md`
- `docs/ADMIN_MANUAL_TEXT.md`
- `docs/WORD_MANUAL_PLAN.md`
- `docs/FAQ.md`
- `docs/OPERATION_FLOW.md`
- `docs/SCREENSHOT_LIST.md`
- `docs/USER_MANUAL_TEMPLATE.md`
- `docs/USER_MANUAL_STRUCTURE.md`

先に必要なcommit:

- Commit 1〜7

commit後に実行するテスト:

- `git diff --check`
- Frontend build任意

想定リスク:

- 手順書と実装の不一致
- 古い数値が残ること

rollback:

- `git revert <commit>`
