# Repository Guide

ProposalPilotの主要ディレクトリと役割。

## Root

| Path | Role |
|---|---|
| `backend/` | FastAPI backend、生成処理、認証、権限、DB、Strategy Engine |
| `frontend/` | Next.js frontend、ガイドUI、管理画面、E2E |
| `docs/` | 製品、運用、設計、営業、Pilot、開発者向けドキュメント |
| `CHANGELOG.md` | リリース履歴 |
| `README.md` | 製品概要と導入ガイド |

## Backend

| Path | Role |
|---|---|
| `backend/app/main.py` | FastAPIアプリ起動とルーター登録 |
| `backend/app/routers/` | APIルーター |
| `backend/app/services/` | PPTX/PDF/Beautiful.aiなどのサービス層 |
| `backend/app/repository_parts/` | Repository分割実装 |
| `backend/app/database/` | DB接続、schema、startup、health |
| `backend/app/models.py` | Pydanticモデルと主要スキーマ |
| `backend/app/config.py` | 環境変数設定 |
| `backend/app/scoping/` | Organization / Workspace分離 |
| `backend/app/strategy_engine/` | Strategy v1、Review、Adapter、Quality、Benchmark、Comparison |
| `backend/tests/` | Backend pytest |
| `backend/tests/strategy_engine/` | Strategy Engine専用テスト |

## Strategy Engine

| File | Role |
|---|---|
| `evaluator.py` | Strategy Brief生成 |
| `rules.py` | カテゴリ、Persona、Story、Pack選定ルール |
| `models.py` | Strategy Brief、Human Review、Presentation Context |
| `review.py` | Human Review Report生成 |
| `adapter.py` | Review ReportからPresentation Contextへ変換 |
| `quality.py` | Proposal Quality Evaluator |
| `benchmark.py` | Evaluation Harness |
| `benchmark_dataset.py` | 評価データセット |
| `comparison.py` | Legacy / Strategy v1比較 |
| `cli.py` | Offline CLI |
| `fixtures.py` | 安全な評価fixture |

## Frontend

| Path | Role |
|---|---|
| `frontend/app/` | Next.js App Routerの静的ページ |
| `frontend/components/` | AppShell、Guided Flow、管理パネルなど |
| `frontend/client-api/` | Backend API呼び出し |
| `frontend/e2e/` | Playwright E2E |
| `frontend/types/` | TypeScript型 |
| `frontend/scripts/` | E2E補助など |

## Docs

| Path | Role |
|---|---|
| `docs/release/` | リリース、運用、RC1 |
| `docs/pilot/` | 実案件評価テンプレート |
| `docs/design/proposal-strategy-engine/` | Strategy Engine設計履歴 |
| `docs/design/` | 販促物、LP、プロトタイプ |
| `docs/brand/` | ブランド基盤 |
| `docs/brand-assets/` | ロゴ、アイコンなど |
| `docs/archive/` | 古いVersion資料 |
| `docs/developer/` | 開発者向け資料 |
