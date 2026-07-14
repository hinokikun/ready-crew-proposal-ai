# Version 23.2 Version Classification

目的: 現在の差分をVersion別に分類し、commit分割の判断材料にします。

注意:

- 推測で断定しないため、機能名、ファイル名、docs名、import関係から分類しています。
- 複数Versionに関係するファイルは「横断」または「人の確認必須」としています。

## Version 17 Beautiful.ai

主な対象:

- `backend/app/config.py`
- `backend/app/routers/beautiful_ai.py`
- `backend/app/services/beautiful_ai_service.py`
- `backend/tests/test_beautiful_ai.py`
- `docs/BEAUTIFUL_AI_INTEGRATION.md`
- `docs/BEAUTIFUL_AI_USER_FLOW.md`
- `frontend/e2e/app.spec.ts`
- `README.md`

判断理由:

- `beautiful_ai`、`BEAUTIFUL_AI`、Beautiful.ai診断、status、mock、enabledの記述を含みます。

## Version 18 Organization / Workspace

主な対象:

- `backend/alembic/versions/20260713_1820_workspace_isolation_acceptance.py`
- `backend/app/context.py`
- `backend/app/dependencies/`
- `backend/app/organization.py`
- `backend/app/routers/organizations.py`
- `backend/app/scope_policy.py`
- `backend/app/scoping/`
- `backend/tests/test_organizations.py`
- `backend/tests/test_workspace_acceptance.py`
- `docs/ORGANIZATION.md`
- `docs/ORGANIZATION_MIGRATION.md`
- `docs/WORKSPACE.md`
- `docs/WORKSPACE_ACCEPTANCE_PLAN.md`
- `docs/WORKSPACE_API_AUDIT.md`
- `docs/WORKSPACE_ISOLATION_AUDIT.md`
- `frontend/client-api/organizations.ts`
- `frontend/components/WorkspaceSwitcher.tsx`
- `frontend/lib/roles.ts`

判断理由:

- Organization / Workspace分離、scope、context、role、workspace acceptanceに関係します。

## Version 19 Presentation Review

主な対象:

- `backend/alembic/versions/20260713_1900_presentation_review_loop.py`
- `backend/alembic/versions/20260713_1910_presentation_review_acceptance.py`
- `backend/app/presentation_review.py`
- `backend/app/routers/presentation_review.py`
- `backend/tests/test_presentation_review.py`
- `docs/PRESENTATION_REVIEW.md`
- `docs/PRESENTATION_REVIEW_ACCEPTANCE.md`
- `docs/PRESENTATION_REVISION.md`
- `frontend/client-api/presentationReview.ts`
- `frontend/components/PresentationReviewPanel.tsx`

判断理由:

- Presentation Review、Revision、Beautiful.ai revision連携に関係します。

## Version 20 Proposal Optimization

主な対象:

- `backend/alembic/versions/20260713_2000_proposal_optimization.py`
- `backend/alembic/versions/20260713_2010_proposal_optimization_acceptance.py`
- `backend/app/proposal_optimization.py`
- `backend/app/routers/proposal_optimization.py`
- `backend/tests/test_proposal_optimization.py`
- `docs/PROPOSAL_OPTIMIZATION.md`
- `docs/PROPOSAL_OPTIMIZATION_ACCEPTANCE.md`
- `docs/BEST_PRACTICES.md`
- `docs/IMPROVEMENT_BACKLOG.md`
- `frontend/client-api/proposalOptimization.ts`
- `frontend/components/ProposalOptimizationPanel.tsx`

判断理由:

- Optimization、Backlog、Best Practice、Recommendationに関係します。

## Version 21 RC / Hardening

主な対象:

- `backend/app/routers/auth.py`
- `backend/app/rate_limit/service.py`
- `backend/app/role_permissions.py`
- `backend/tests/test_auth_permissions.py`
- `docs/LOGIN_GUIDE.md`
- `docs/ROLE_PERMISSIONS.md`
- `docs/ROLE_PERMISSION_AUDIT.md`
- `frontend/components/AuthGate.tsx`
- `frontend/components/AdminUsersPanel.tsx`
- `frontend/components/PermissionNotice.tsx`
- `frontend/lib/auth.ts`
- `frontend/lib/storage.ts`

判断理由:

- login_mode、role表示、rate limit、権限表示、UAT制御に関係します。

## Version 22 Architecture Refactoring

主な対象:

- `backend/app/database/`
- `backend/app/db.py`
- `backend/app/repository_parts/`
- `backend/app/repositories.py`
- `backend/app/router_registry.py`
- `backend/app/services/pptx_parts/`
- `backend/app/services/pptx_theme.py`
- `backend/app/services/pptx_service.py`
- `backend/tests/snapshots/`
- `backend/tests/test_pptx_structure_regression.py`
- `docs/APPSHELL_DECOMPOSITION.md`
- `docs/APPSHELL_UI_DECOMPOSITION.md`
- `docs/ARCHITECTURE_SCORE.md`
- `docs/PPTX_VISUAL_REGRESSION.md`
- `docs/REFACTORING_BASELINE.md`
- `docs/REFACTORING_RESULTS.md`
- `docs/V22_2_BASELINE.md`
- `docs/V22_2_REFACTORING_RESULTS.md`
- `frontend/app/styles/`
- `frontend/app/globals.css`
- `frontend/components/app-shell/`
- `frontend/components/AppShell.tsx`
- `scripts/compare_pptx_previews.py`
- `scripts/render_pptx_preview.py`

判断理由:

- 巨大ファイル分割、CSS分割、PPTX構造回帰、AppShell分割に関係します。

## Version 23 Simple Guided UI

主な対象:

- `frontend/components/guided-flow/`
- `frontend/app/styles/guided-flow.css`
- `frontend/components/AppShell.tsx`
- `frontend/components/Header.tsx`
- `frontend/e2e/app.spec.ts`
- `docs/SIMPLE_UI_SPEC.md`
- `docs/GUIDED_FLOW.md`
- `docs/QUALITY_GATE_UI.md`
- `docs/BEAUTIFUL_AI_USER_FLOW.md`
- `docs/UAT_CHECKLIST.md`
- `README.md`

判断理由:

- 7ステップ、通常モード、詳細モード、提出前チェック、Beautiful.ai簡易表示に関係します。

## Version 23.1 Documentation

主な対象:

- `docs/V23_1_HANDOFF_STATUS.md`
- `docs/V23_0_CHANGE_SUMMARY.md`
- `docs/V23_1_GITHUB_PUSH_GUIDE.md`
- `docs/V23_1_GITHUB_ACTIONS_GUIDE.md`
- `docs/V23_1_VERCEL_GUIDE.md`
- `docs/V23_1_RENDER_GUIDE.md`
- `docs/V23_1_BROWSER_VERIFICATION.md`
- `docs/V23_1_UAT_SAMPLE_CASES.md`
- `docs/V23_1_SIMPLE_UAT.md`
- `docs/V23_1_BUG_REPORT_TEMPLATE.md`
- `docs/USER_MANUAL_TEXT.md`
- `docs/ADMIN_MANUAL_TEXT.md`
- `docs/WORD_MANUAL_PLAN.md`

判断理由:

- GitHub反映、本番確認、UAT、マニュアル原稿の引き継ぎ資料です。

## Version不明 / 横断

主な対象:

- `backend/app/ai_watch.py`
- `backend/app/analytics/repositories.py`
- `backend/app/analytics/services.py`
- `backend/app/integrations.py`
- `backend/app/knowledge/repositories.py`
- `backend/app/knowledge/services.py`
- `backend/app/learning/analyzer.py`
- `backend/app/learning/repositories.py`
- `backend/app/learning/services.py`
- `backend/app/orchestrator.py`
- `backend/app/project_lifecycle.py`
- `backend/app/prompts/repositories.py`
- `backend/app/prompts/services.py`
- `backend/app/quality_gates.py`
- `backend/app/reviews.py`
- `backend/app/routers/analytics.py`
- `backend/app/routers/knowledge.py`
- `backend/app/routers/learning.py`
- `backend/app/routers/logs.py`
- `backend/app/routers/orchestrator.py`
- `backend/app/routers/pilot.py`
- `backend/app/routers/projects.py`
- `backend/app/routers/prompts.py`
- `backend/app/routers/quality_gates.py`
- `backend/app/routers/reviews.py`
- `backend/app/routers/users.py`
- `backend/app/routers/workspace.py`
- `backend/app/workspace/repositories.py`
- `docs/BACKUP_RESTORE.md`
- `docs/DEPLOYMENT_VERIFICATION.md`
- `docs/INCIDENT_RESPONSE.md`
- `docs/OPERATIONS.md`
- `docs/RELEASE.md`
- `docs/SECURITY.md`
- `docs/TESTING.md`
- `scripts/smoke_test.py`

判断理由:

- 複数Versionのハードニング、運用、監査、既存機能調整が混在している可能性があります。
- commit前に差分内容を人が確認してください。

## 一時ファイル / 生成物 / commit対象外候補

明確な巨大生成物は未確認です。

注意候補:

- `backend/tests/snapshots/*.json`: 回帰テスト用snapshotの可能性が高いが、人の確認後commit推奨
- `scripts/compare_pptx_previews.py`: visual regression用scriptの可能性が高いが、人の確認後commit推奨
- `scripts/render_pptx_preview.py`: visual regression用scriptの可能性が高いが、人の確認後commit推奨
