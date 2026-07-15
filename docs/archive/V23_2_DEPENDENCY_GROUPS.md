# Version 23.2 Dependency Groups

目的: commitを分けても途中で壊れにくい依存グループを整理します。

## Group A: Backend DB / Migration / Models

含めるもの:

- `backend/app/database/`
- `backend/app/db.py`
- `backend/app/models.py`
- `backend/alembic/versions/*.py`
- `backend/migrations/README.md`

依存:

- routers/services/repositoriesがDB schemaを参照します。
- migrationは既存DBに影響するため、commit前に人の確認が必要です。

## Group B: Backend Scope / Auth / Organization

含めるもの:

- `backend/app/context.py`
- `backend/app/dependencies/`
- `backend/app/organization.py`
- `backend/app/scope_policy.py`
- `backend/app/scoping/`
- `backend/app/role_permissions.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/organizations.py`
- `backend/app/routers/users.py`
- `backend/tests/test_auth_permissions.py`
- `backend/tests/test_organizations.py`
- `backend/tests/test_workspace_acceptance.py`

依存:

- Organization / Workspace分離はBackend API側の権限制御に依存します。
- Frontend WorkspaceSwitcherより先にBackendを安定させます。

## Group C: Backend Feature Services / Routers

含めるもの:

- `backend/app/presentation_review.py`
- `backend/app/proposal_optimization.py`
- `backend/app/routers/presentation_review.py`
- `backend/app/routers/proposal_optimization.py`
- `backend/app/routers/beautiful_ai.py`
- `backend/app/services/beautiful_ai_service.py`
- `backend/app/ai_watch.py`
- `backend/app/analytics/`
- `backend/app/knowledge/`
- `backend/app/learning/`
- `backend/app/prompts/`
- `backend/app/quality_gates.py`
- `backend/app/reviews.py`
- `backend/app/project_lifecycle.py`
- 関連 tests

依存:

- router registry / main.py が各routerを登録します。
- Presentation Review / Proposal Optimization はFrontend panelsに依存されます。

## Group D: Backend Repository / PPTX Refactoring

含めるもの:

- `backend/app/repositories.py`
- `backend/app/repository_parts/`
- `backend/app/services/pptx_service.py`
- `backend/app/services/pptx_parts/`
- `backend/app/services/pptx_theme.py`
- `backend/tests/test_pptx_structure_regression.py`
- `backend/tests/snapshots/`

依存:

- 既存router/serviceがrepositoryを参照します。
- PPTX snapshotは意図した出力構造差分か人が確認してください。

## Group E: Frontend Client API / Types / Auth

含めるもの:

- `frontend/client-api/`
- `frontend/types/app.ts`
- `frontend/lib/api.ts`
- `frontend/lib/auth.ts`
- `frontend/lib/storage.ts`
- `frontend/lib/roles.ts`
- `frontend/components/AuthGate.tsx`
- `frontend/components/Header.tsx`
- `frontend/components/PermissionNotice.tsx`

依存:

- UI componentsがclient-api/types/authに依存します。
- Backend API変更と同じcommitまたは直後に入れると安全です。

## Group F: Frontend AppShell / Styles / Panels

含めるもの:

- `frontend/components/AppShell.tsx`
- `frontend/components/app-shell/`
- `frontend/components/PresentationReviewPanel.tsx`
- `frontend/components/ProposalOptimizationPanel.tsx`
- `frontend/components/UatModePanel.tsx`
- `frontend/components/WorkspaceSwitcher.tsx`
- `frontend/app/globals.css`
- `frontend/app/styles/`

依存:

- AppShellが分割先components/stylesをimportします。
- CSS分割ファイルが欠けるとbuildが壊れます。

## Group G: Simple Guided UI

含めるもの:

- `frontend/components/guided-flow/`
- `frontend/app/styles/guided-flow.css`
- `frontend/components/AppShell.tsx`
- `frontend/components/Header.tsx`

依存:

- AppShellにGuided Flow表示の組み込みがあります。
- Headerに通常/詳細モード表示の変更がある可能性があります。

## Group H: Frontend E2E

含めるもの:

- `frontend/e2e/app.spec.ts`

依存:

- UI変更後に入れると意図が読みやすいです。
- Group E/F/Gに依存します。

## Group I: Docs

含めるもの:

- `README.md`
- `docs/*.md`

依存:

- アプリ動作には直接影響しません。
- 実装commit後にまとめるとreviewしやすいです。
