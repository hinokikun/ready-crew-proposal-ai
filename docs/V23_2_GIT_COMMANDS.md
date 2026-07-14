# Version 23.2 Git Commands Draft

目的: `git add .` を使わず、安全にcommitを分けるためのコマンド案です。

重要:

- このファイル内のコマンドは提案です。
- この作業では実行していません。
- 各commit前に必ず `git diff --cached` を確認してください。

## 共通の事前確認

```bat
cd C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai
git status --short
git diff --check
```

## Commit 1: Organization / Workspace基盤

```bat
git add backend\alembic\versions\20260713_1820_workspace_isolation_acceptance.py
git add backend\app\context.py
git add backend\app\dependencies
git add backend\app\organization.py
git add backend\app\routers\organizations.py
git add backend\app\scope_policy.py
git add backend\app\scoping
git add backend\app\role_permissions.py
git add backend\tests\test_organizations.py
git add backend\tests\test_workspace_acceptance.py
git add frontend\client-api\organizations.ts
git add frontend\components\WorkspaceSwitcher.tsx
git add frontend\lib\roles.ts
git add docs\ORGANIZATION.md
git add docs\WORKSPACE.md
git add docs\ORGANIZATION_MIGRATION.md
git add docs\WORKSPACE_ACCEPTANCE_PLAN.md
git add docs\WORKSPACE_API_AUDIT.md
git add docs\WORKSPACE_ISOLATION_AUDIT.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Add organization and workspace isolation foundation"
```

## Commit 2: Presentation Review / Revision

```bat
git add backend\alembic\versions\20260713_1900_presentation_review_loop.py
git add backend\alembic\versions\20260713_1910_presentation_review_acceptance.py
git add backend\app\presentation_review.py
git add backend\app\routers\presentation_review.py
git add backend\tests\test_presentation_review.py
git add frontend\client-api\presentationReview.ts
git add frontend\components\PresentationReviewPanel.tsx
git add docs\PRESENTATION_REVIEW.md
git add docs\PRESENTATION_REVIEW_ACCEPTANCE.md
git add docs\PRESENTATION_REVISION.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Add presentation review and revision workflow"
```

## Commit 3: Proposal Optimization

```bat
git add backend\alembic\versions\20260713_2000_proposal_optimization.py
git add backend\alembic\versions\20260713_2010_proposal_optimization_acceptance.py
git add backend\app\proposal_optimization.py
git add backend\app\routers\proposal_optimization.py
git add backend\tests\test_proposal_optimization.py
git add frontend\client-api\proposalOptimization.ts
git add frontend\components\ProposalOptimizationPanel.tsx
git add docs\PROPOSAL_OPTIMIZATION.md
git add docs\PROPOSAL_OPTIMIZATION_ACCEPTANCE.md
git add docs\BEST_PRACTICES.md
git add docs\IMPROVEMENT_BACKLOG.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Add proposal optimization workflow"
```

## Commit 4: Beautiful.ai 本番確認

```bat
git add backend\app\config.py
git add backend\app\routers\beautiful_ai.py
git add backend\app\services\beautiful_ai_service.py
git add backend\tests\test_beautiful_ai.py
git add docs\BEAUTIFUL_AI_INTEGRATION.md
git add docs\BEAUTIFUL_AI_USER_FLOW.md
git add README.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Harden Beautiful.ai production verification"
```

確認:

- `BEAUTIFUL_AI...=` の右側に実キーがないこと。
- README/docs内の値がplaceholderであること。

## Commit 5: Architecture Refactoring

```bat
git add backend\app\database
git add backend\app\db.py
git add backend\app\repository_parts
git add backend\app\repositories.py
git add backend\app\router_registry.py
git add backend\app\services\pptx_parts
git add backend\app\services\pptx_theme.py
git add backend\app\services\pptx_service.py
git add frontend\app\globals.css
git add frontend\app\styles
git add frontend\components\app-shell
git add frontend\components\AppShell.tsx
git add backend\tests\test_pptx_structure_regression.py
git add backend\tests\snapshots
git add scripts\compare_pptx_previews.py
git add scripts\render_pptx_preview.py
git add docs\APPSHELL_DECOMPOSITION.md
git add docs\APPSHELL_UI_DECOMPOSITION.md
git add docs\ARCHITECTURE_SCORE.md
git add docs\PPTX_VISUAL_REGRESSION.md
git add docs\REFACTORING_BASELINE.md
git add docs\REFACTORING_RESULTS.md
git add docs\V22_2_BASELINE.md
git add docs\V22_2_REFACTORING_RESULTS.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Split large frontend and backend modules"
```

## Commit 6: Simple Guided UI

```bat
git add frontend\components\guided-flow
git add frontend\app\styles\guided-flow.css
git add frontend\components\AppShell.tsx
git add frontend\components\Header.tsx
git add frontend\e2e\app.spec.ts
git add docs\SIMPLE_UI_SPEC.md
git add docs\GUIDED_FLOW.md
git add docs\QUALITY_GATE_UI.md
git add docs\UAT_CHECKLIST.md
git add README.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Add simple guided proposal workflow"
```

注意:

- `AppShell.tsx` と `README.md` は複数commit候補にまたがります。
- 実際には `git add -p` で分けるか、Commit 5/6をまとめる判断が必要です。

## Commit 7: Tests and smoke checks

```bat
git add frontend\e2e\app.spec.ts
git add backend\tests\test_audit_logs.py
git add backend\tests\test_auth_permissions.py
git add backend\tests\test_beautiful_ai.py
git add backend\tests\test_project_lifecycle.py
git add backend\tests\test_quality_gates.py
git add backend\tests\test_organizations.py
git add backend\tests\test_presentation_review.py
git add backend\tests\test_proposal_optimization.py
git add backend\tests\test_workspace_acceptance.py
git add scripts\smoke_test.py
git add docs\TESTING.md
git add docs\DEPLOYMENT_VERIFICATION.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Add regression and deployment verification tests"
```

注意:

- 既に前commitで追加したtestを再度指定しても、stage対象がなければ問題ありません。
- 実際のcommit分割では重複指定に注意してください。

## Commit 8: Documentation and manuals

```bat
git add docs\V23_1_HANDOFF_STATUS.md
git add docs\V23_0_CHANGE_SUMMARY.md
git add docs\V23_1_GITHUB_PUSH_GUIDE.md
git add docs\V23_1_GITHUB_ACTIONS_GUIDE.md
git add docs\V23_1_VERCEL_GUIDE.md
git add docs\V23_1_RENDER_GUIDE.md
git add docs\V23_1_BROWSER_VERIFICATION.md
git add docs\V23_1_UAT_SAMPLE_CASES.md
git add docs\V23_1_SIMPLE_UAT.md
git add docs\V23_1_BUG_REPORT_TEMPLATE.md
git add docs\V23_2_CHANGESET_AUDIT.md
git add docs\V23_2_VERSION_CLASSIFICATION.md
git add docs\V23_2_COMMIT_CLASSIFICATION.md
git add docs\V23_2_SECRET_AUDIT.md
git add docs\V23_2_GITIGNORE_RECOMMENDATIONS.md
git add docs\V23_2_DEPENDENCY_GROUPS.md
git add docs\V23_2_SAFE_COMMIT_PLAN.md
git add docs\V23_2_GIT_COMMANDS.md
git add docs\V23_2_TEST_MATRIX.md
git add docs\V23_2_CLOUD_RELEASE_SEQUENCE.md
git add docs\V23_2_ROLLBACK_PLAN.md
git add docs\V23_2_HUMAN_ACTION_CHECKLIST.md
git add docs\V23_2_DOCUMENT_CONFLICTS.md
git add docs\USER_MANUAL_TEXT.md
git add docs\ADMIN_MANUAL_TEXT.md
git add docs\WORD_MANUAL_PLAN.md
git add docs\FAQ.md
git add docs\OPERATION_FLOW.md
git add docs\SCREENSHOT_LIST.md
git add docs\USER_MANUAL_TEMPLATE.md
git add docs\USER_MANUAL_STRUCTURE.md
git diff --cached --stat
git diff --cached
git status --short
git commit -m "Add deployment handoff and UAT documentation"
```

## 最後のpush前確認

```bat
git status --short
git log --oneline -8
```

すべて問題なければ:

```bat
git push origin main
```
