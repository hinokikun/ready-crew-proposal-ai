# Version 23.2 Commit Classification

目的: 変更ファイルを commit 安全性の観点で A/B/C/D に分類します。

## 区分

- A. commit必須: アプリの動作に必要
- B. commit推奨: 運用・説明に必要
- C. 人の確認後にcommit: snapshot、migration、workflow相当、生成に近い資料など
- D. commit禁止・除外候補: 秘密情報、cache、生成物、個人PC固有ファイル

## 件数目安

| 区分 | 件数目安 | 備考 |
|---|---:|---|
| A commit必須 | 100 | Backend/Frontend実装、tests、migrationを含む |
| B commit推奨 | 45 | docs、README、運用資料 |
| C 人の確認後にcommit | 17 | snapshots、scripts、migration、横断docsの一部 |
| D commit禁止・除外候補 | 0 | 明確な `.env`、cache、DB、PDF/PPTX は未検出 |

## A. commit必須

| ファイル/グループ | 関連Version | 役割 | commit理由 | 人の確認 | 依存先/注意 |
|---|---|---|---|---|---|
| `backend/app/context.py` | V18 | request context | Workspace/Organization分離に必要 | 要 | dependencies/context |
| `backend/app/database/` | V22 | DB接続/health/migration/schema/startup分割 | `db.py`分割後の実体 | 要 | `backend/app/db.py` |
| `backend/app/dependencies/` | V18 | FastAPI依存関係 | scope/auth contextに必要 | 要 | routers |
| `backend/app/health.py` | V18/V22 | health/ready情報 | Render確認に必要 | 要 | main/router registry |
| `backend/app/organization.py` | V18 | Organization/Workspace logic | 分離仕様に必要 | 要 | routers/organizations |
| `backend/app/presentation_review.py` | V19 | Presentation Review service | Review/Revisionに必要 | 要 | routers/presentation_review |
| `backend/app/proposal_optimization.py` | V20 | Optimization service | TOP5改善に必要 | 要 | routers/proposal_optimization |
| `backend/app/repository_parts/` | V22 | Repository分割 | `repositories.py`分割後の実体 | 要 | repositories.py |
| `backend/app/role_permissions.py` | V21 | role表示/権限 | Login/role hardeningに必要 | 要 | auth/users |
| `backend/app/router_registry.py` | V22 | router登録整理 | Route漏れ防止に必要 | 要 | main.py |
| `backend/app/routers/organizations.py` | V18 | Organization API | Workspace切替に必要 | 要 | organization.py |
| `backend/app/routers/presentation_review.py` | V19 | Presentation Review API | Review UIに必要 | 要 | presentation_review.py |
| `backend/app/routers/proposal_optimization.py` | V20 | Optimization API | Optimization UIに必要 | 要 | proposal_optimization.py |
| `backend/app/scope_policy.py` | V18 | scope policy | Organization越境防止に必要 | 要 | scoping |
| `backend/app/scoping/` | V18 | scope service | Workspace分離に必要 | 要 | repositories/routers |
| `backend/app/services/pptx_parts/` | V22 | PPTX service分割 | PPTX生成維持に必要 | 要 | pptx_service.py |
| `backend/app/services/pptx_theme.py` | V22 | PPTX theme | PPTX生成維持に必要 | 要 | pptx_parts |
| `frontend/app/styles/` | V22/V23 | CSS分割/Guided Flow | `globals.css`分割後に必要 | 要 | globals.css |
| `frontend/client-api/*.ts` | V18/V19/V20 | Frontend API client | UI panelsから利用 | 要 | AppShell/panels |
| `frontend/components/app-shell/` | V22 | AppShell分割 | AppShell軽量化後に必要 | 要 | AppShell.tsx |
| `frontend/components/guided-flow/` | V23 | 7ステップUI | Simple Guided UIに必要 | 要 | AppShell.tsx |
| `frontend/components/PresentationReviewPanel.tsx` | V19 | Review UI | STEP6/詳細表示に必要 | 要 | client-api/presentationReview |
| `frontend/components/ProposalOptimizationPanel.tsx` | V20 | Optimization UI | STEP6/詳細表示に必要 | 要 | client-api/proposalOptimization |
| `frontend/components/UatModePanel.tsx` | V20.3 | UAT mode | UAT確認に必要 | 要 | AppShell |
| `frontend/components/WorkspaceSwitcher.tsx` | V18 | Workspace切替 | Organization/Workspaceに必要 | 要 | client-api/organizations |
| `frontend/lib/roles.ts` | V21 | role表示 | 権限表示に必要 | 要 | Header/AuthGate |
| modified runtime files | 横断 | 既存ファイル更新 | 新規分割先を参照するため必要 | 要 | diff確認必須 |
| backend tests | 各Version | 回帰テスト | CIで必要 | 要 | app modules |
| frontend e2e | 各Version | E2E | CI/UATで必要 | 要 | UI selectors |

## B. commit推奨

| ファイル/グループ | 関連Version | 役割 | commit理由 | 人の確認 | 注意 |
|---|---|---|---|---|---|
| `README.md` | 横断 | 概要/運用 | 本番運用に必要 | 要 | 秘密値なし確認 |
| `docs/ARCHITECTURE.md` | V22/V23 | 構成 | 保守に必要 | 要 | 最新構成と一致確認 |
| `docs/SECURITY.md` | 横断 | セキュリティ | 運用に必要 | 要 | 実秘密値なし確認 |
| `docs/OPERATIONS.md` | 横断 | 運用 | 本番手順に必要 | 要 | Cloud手順確認 |
| `docs/RELEASE.md` | 横断 | リリース | 手順に必要 | 要 | V23.2計画と矛盾確認 |
| `docs/TESTING.md` | 横断 | テスト | CI/ローカル実行に必要 | 要 | コマンド妥当性確認 |
| `docs/SIMPLE_UI_SPEC.md` | V23 | Simple UI仕様 | UATに必要 | 要 | UI実装と一致確認 |
| `docs/GUIDED_FLOW.md` | V23 | Flow説明 | UAT/保守に必要 | 要 | 実画面と一致確認 |
| `docs/QUALITY_GATE_UI.md` | V23 | 提出前チェック | UATに必要 | 要 | Backend同期記述確認 |
| `docs/BEAUTIFUL_AI_USER_FLOW.md` | V23 | Beautiful.ai導線 | UATに必要 | 要 | 技術詳細出し過ぎ注意 |
| `docs/V23_1_*.md` | V23.1 | 引き継ぎ | 人間作業に必要 | 要 | 数値はV23.2前時点 |
| `docs/USER_MANUAL_TEXT.md` | V23.1 | 利用者マニュアル原稿 | Word化準備 | 要 | UAT後に調整 |
| `docs/ADMIN_MANUAL_TEXT.md` | V23.1 | 管理者マニュアル原稿 | Word化準備 | 要 | 管理項目確認 |
| `docs/WORD_MANUAL_PLAN.md` | V23.1 | Word化計画 | UAT後に必要 | 要 | ページ数は見積 |

## C. 人の確認後にcommit

| ファイル/グループ | 関連Version | 役割 | commit理由 | 人の確認 | 注意 |
|---|---|---|---|---|---|
| `backend/alembic/versions/*.py` | V18/V19/V20 | migration | DB移行に必要な可能性 | 必須 | 既存DBで安全か確認 |
| `backend/tests/snapshots/*.json` | V22 | PPTX回帰snapshot | Visual regressionに必要 | 必須 | 意図した出力差分か確認 |
| `scripts/compare_pptx_previews.py` | V22 | PPTX比較 | 回帰確認に必要 | 必須 | 生成物ではなくscript |
| `scripts/render_pptx_preview.py` | V22 | PPTX preview | 回帰確認に必要 | 必須 | 生成物ではなくscript |
| `scripts/smoke_test.py` | 横断 | Cloud smoke | リリース確認に必要 | 必須 | URL/秘密値なし確認 |
| 大量docs | V21-V23 | 監査/運用 | 必要資料だが量が多い | 必須 | commitを分ける |

## D. commit禁止・除外候補

明確な除外対象は現在の `git status` には見当たりません。

ただし、今後出た場合はcommit禁止:

- `.env`
- `.env.local`
- `node_modules/`
- `.next/`
- `__pycache__/`
- `.pytest_cache/`
- `test-results/`
- `playwright-report/`
- `*.db`
- `*.sqlite`
- `*.pptx`
- `*.pdf`
- `*.log`
- 実スクリーンショット
- 実顧客情報を含むファイル
