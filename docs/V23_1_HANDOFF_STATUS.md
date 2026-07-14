# Version 23.1 Handoff Status

作成日: 2026-07-14
目的: Version 23.0 Simple Guided UI のあと、人間が GitHub 反映、本番デプロイ、ブラウザ確認、UAT を安全に進めるための現在状態メモです。

## 重要方針

- このファイルは引き継ぎ用です。
- Version 23.1 ではコード、UI、API、DB、権限、Beautiful.ai 仕様、PowerPoint/PDF 仕様は変更しません。
- 自動 commit、自動 push、本番環境変更は行いません。
- 秘密情報の値は記録しません。

## Git 状態

- Branch: `main`
- HEAD commit: `aecbc6b421b5826c9704516eab891b752d329338`
- HEAD summary: `aecbc6b Document Beautiful.ai production verification`

## Working Tree Summary

確認時点の `git status --porcelain` 概要:

- 未コミット合計: 162 件
- 変更済みまたは stage 対象候補: 69 件
- 未追跡: 93 件
- 削除: 0 件

注意:

- 作業ツリーには Version 23.0 以前からの大量の変更が残っています。
- 上記の未追跡数には、この Version 23.1 で追加した引き継ぎドキュメント 13 件も含みます。
- commit 前に、今回含めるファイルを必ず人間が確認してください。
- `git add .` は避け、必要なファイルだけを明示的に追加してください。

## 主な変更済みファイル例

- `README.md`
- `frontend/components/AppShell.tsx`
- `frontend/components/Header.tsx`
- `frontend/app/globals.css`
- `frontend/e2e/app.spec.ts`
- `frontend/lib/api.ts`
- `backend/app/main.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/beautiful_ai.py`
- `backend/app/services/beautiful_ai_service.py`
- `backend/tests/test_beautiful_ai.py`
- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/OPERATIONS.md`
- `docs/RELEASE.md`

## 主な未追跡ファイル例

- `backend/alembic/versions/20260713_1820_workspace_isolation_acceptance.py`
- `backend/alembic/versions/20260713_1900_presentation_review_loop.py`
- `backend/alembic/versions/20260713_1910_presentation_review_acceptance.py`
- `backend/alembic/versions/20260713_2000_proposal_optimization.py`
- `backend/alembic/versions/20260713_2010_proposal_optimization_acceptance.py`
- `backend/app/context.py`
- `backend/app/database/`
- `backend/app/dependencies/`
- `backend/app/health.py`
- `backend/app/organization.py`
- `backend/app/presentation_review.py`

## Version 23.1 で追加した未追跡ドキュメント

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

## 秘密情報確認

確認結果:

- `.env` 系ファイルが `git status` に出ていないこと: 確認済み
- `frontend/api` が再作成されていないこと: 確認済み
- `frontend/app/**/route.ts` 数: 0
- Vercel Serverless Functions 想定数: 0
- 差分内の秘密情報らしきパターン:
  - `OPENAI_API_KEY=`: 0
  - `DATABASE_URL=`: 0
  - `Authorization: Bearer ...`: 0
  - `password=` または `password:` の値らしきもの: 0
  - `token=` または `token:` の値らしきもの: 0
  - `BEAUTIFUL_AI...KEY=`: 1 件検出

補足:

- `BEAUTIFUL_AI...KEY=` は Beautiful.ai 関連ドキュメントまたは設定説明の可能性があります。
- commit 前に `git diff` で値が実キーではなくプレースホルダーであることを人間が確認してください。
- 秘密情報の値はこのドキュメントには記録していません。

## Vercel Hobby 前提

- `frontend/app/**/route.ts` が 0 件のため、Frontend 側 Route Handler による Serverless Function は 0 想定です。
- `frontend/api` は存在しません。
- Vercel Hobby の Serverless Functions 上限に抵触しない構成を維持しています。

## 次に人が行うこと

1. `docs/V23_1_GITHUB_PUSH_GUIDE.md` に従って、commit 対象を確認します。
2. `git diff` で秘密情報が含まれないことを確認します。
3. 必要なファイルだけを `git add` します。
4. GitHub へ push します。
5. GitHub Actions、Vercel、Render、本番ブラウザ UAT の順に確認します。
