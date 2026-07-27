# Current State Audit

調査日: 2026-07-23  
対象: Ready Crew Proposal AI / Version 80までの作業ツリー  
Git: branch `main`, HEAD `91285ed`  
注意: 作業ツリーにはVersion 80以前からの未コミット・未追跡ファイルが混在している。監査では存在するコードと文書を読み取り、実装済みと構想を分離した。

## Frontend

| 項目 | 状態 | 根拠 | 備考 |
|---|---|---|---|
| Next.js | 実装済み | `frontend/package.json` | Next.js 15系、React 19系。App Router構成。 |
| App Router | 実装済み | `frontend/app/page.tsx`, `frontend/app/layout.tsx` | ルートは単一ページ中心。 |
| AppShell | 実装済み / 技術的負債 | `frontend/components/AppShell.tsx` | 多機能が残り、責務が大きい。Version80でサイドバーを追加したが完全分割は未完了。 |
| 認証後レイアウト | 実装済み | `AuthGate.tsx`, `AppShell.tsx` | ログイン後にAppShellを表示。 |
| 固定サイドバー | 部分実装 | `proposal-experience/ProposalExperienceNav.tsx` | サイドバー、折りたたみ、モバイルドロワーあり。URLルーティングではなくビュー切替。 |
| ホーム | 部分実装 | `ProposalAgentDashboard.tsx`, `GuidedFlow.tsx` | 既存ダッシュボードをV80ビューへ配置。情報整理は継続課題。 |
| 新規提案 / Prompt Builder | UIのみ | `ProposalExperienceStudio.tsx` | ステップ入力、クイック入力、不足情報表示あり。DB保存は未接続。 |
| Story確認 | UIのみ | `ProposalExperienceStudio.tsx` | Storyタイプ、スライド構成を表示。実Strategy Engineとは未統合。 |
| 3ペインエディター | UIのみ | `ProposalExperienceStudio.tsx` | スライド一覧、プレビュー、AI改善案を表示。PPTX編集データ保存は未実装。 |
| Presentation Designer | 部分実装 | `ProposalExperienceStudio.tsx`, `frontend/lib/pptx.ts` | 8テンプレート選択とPPTXリクエスト連携あり。全スライド適用は限定的。 |
| Proposal Agent | 部分実装 | `ProposalAgentDashboard.tsx`, `frontend/client-api/proposalAgent.ts` | Dashboard、Memory系APIが存在。 |
| Proposal Intelligence | 部分実装 | Dashboard系UIとdocs | KPI、優先度、改善レポートが混在。統一モデルは未完了。 |
| Proposal Copilot | 部分実装 | `components/copilot/` | UI部品あり。全画面横断の対話体験としては未統合。 |
| 業務改善 | 実装済み | `BusinessImprovementReportPanel.tsx`, `logs.ts` | レポート、CSV、ダッシュボード系APIあり。 |
| 管理画面 | 実装済み / 複雑 | `Admin*Panel.tsx` | ユーザー、監査、診断、UAT、分析など多数。 |
| Beautiful.ai画面 | 実装済み | `BeautifulAiStatusCard.tsx`, `GuidedFlow.tsx`, `AppShell.tsx` | status、diagnostics、作成、URL処理あり。 |
| PPTX / PDF導線 | 実装済み | `frontend/lib/pptx.ts`, `frontend/lib/pdf.ts` | 既存生成APIを利用。 |
| 状態管理 | 部分実装 | `useState`, `localStorage` | Zustand等はなく、AppShell中心。Autosaveは限定的。 |
| CSS / Design System | 部分実装 | `frontend/app/styles/*.css`, `docs/design-system` | 複数CSSが存在。V80用CSS追加。統一は継続課題。 |
| レスポンシブ | 部分実装 | CSS media query, E2E | 360px系のE2Eあり。全管理画面は要継続確認。 |
| アクセシビリティ | 部分実装 | aria-label, focus-visible, E2E | 主要導線は対応。包括監査は未完了。 |
| E2E | 実装済み | `frontend/e2e/app.spec.ts` | 66件。ログイン、Guided Flow、Beautiful.ai、V80 sidebarなど。 |

## Backend

| 項目 | 状態 | 根拠 | 備考 |
|---|---|---|---|
| FastAPI | 実装済み | `backend/app/main.py`, `router_registry.py` | router files 27、route handlers 158。 |
| 認証 | 実装済み | `auth.py`, `routers/auth.py` | JWT、role、初期admin seedあり。 |
| User / Workspace / Organization | 実装済み | `database/schema.py`, `routers/users.py`, `organizations.py`, `workspace.py` | Organization / Workspace境界のテストあり。 |
| Project / CRM | 実装済み | `routers/projects.py`, `repository_parts/crm.py` | ライフサイクル、outcome、handoffあり。 |
| Proposal生成 | 実装済み | `models.py`, `proposal_prompts.py`, `openai_service.py` | 同期生成中心。カテゴリ汎用化済み。 |
| Strategy Engine | API未接続中心 / オフライン実装 | `app/strategy_engine/` | CLI、adapter、quality、benchmark、comparisonあり。既定フローはLegacy。 |
| Sales Assistant | 部分実装 | `sales_assistant/`, `routers/sales_assistant.py` | Feature Flag付き。Proposal Preview / Export APIあり。 |
| Proposal Agent | 部分実装 | `routers/proposal_agent.py` | Dashboard、memory API。未追跡ファイルとして存在。 |
| PPTX生成 | 実装済み | `services/pptx_service.py`, `pptx_parts/`, `pptx_design/` | python-pptx。V80でdesign_template追加。 |
| PDF生成 | 実装済み | `services/pdf_service.py` | 見積PDF導線あり。 |
| Beautiful.ai | 実装済み | `services/beautiful_ai_service.py`, `routers/beautiful_ai.py` | Prompt API、diagnostics、URL正規化、履歴あり。 |
| 見積 | 実装済み | proposal profile / PDF / AppShell logic | カテゴリ別見積項目あり。 |
| 履歴 / ログ | 実装済み | `routers/logs.py`, `admin_observability.py` | 生成履歴、監査ログ、業務改善CSVあり。 |
| 業務改善データ | 実装済み | `business_improvement_reports` | Version 71系。 |
| Version80 design_template | 実装済み | `PptxDownloadRequest`, `PptxContext` | `brand_settings`は受け取り可能だが反映は限定。 |
| Migration | 実装済み / 要整理 | `backend/alembic/versions` | 10件。Training / Proposal Agent系の未追跡migrationあり。 |
| 外部API | 実装済み | OpenAI, Beautiful.ai | 失敗時の安全化あり。費用監視は未実装。 |
| バックグラウンド処理 | 未実装に近い | action_queue tableは存在 | 長時間生成は同期処理中心。Job化が必要。 |
| テスト | 実装済み | `backend/tests` | 371件収集。 |

## Documentation

| 領域 | 状態 | 備考 |
|---|---|---|
| README | 実装済み / 肥大化傾向 | Version 80説明あり。 |
| docs/design | 実装済み / 多数 | Brand、LP、Prototype、Presentation Pack、V80 docsが混在。 |
| Version 41〜48 | 設計・オフライン実装中心 | Strategy Engine系列文書あり。 |
| Version 49〜54 | 部分実装 | Sales Assistant、Proposal Preview、Export文書あり。 |
| Version 60〜71 | 部分実装 / 一部実装済み | Intelligence、研修提出、業務改善系が混在。 |
| 重複 | あり | Release、UAT、Design、Strategy関連で重複あり。 |
| 古い記述 | あり | ArchiveされたV23〜V25文書、実装状態とズレる箇所あり。 |

## 実装済み

- ログイン、初期admin seed、Role制御。
- Organization / Workspace分離。
- 案件入力、提案生成、Quality Gate。
- PPTX / PDF出力。
- Beautiful.ai status、diagnostics、Prompt API作成、URL解決。
- 作成履歴、監査ログ、業務改善レポート、CSV。
- Version80固定サイドバー、Prompt Builder UI、Story/Designer/3ペインUI、PPTテンプレート選択。

## 部分実装

- Proposal Studio: UIのみで、永続化とPPTX差分編集は未完了。
- Presentation Designer: テンプレート選択は反映、全レイアウトの自動選択は未完了。
- Brand Settings: request modelはあるが、ロゴ、フォント、全ページ反映は未完了。
- Strategy v1 / Sales Assistant: Offline/Feature Flag中心。Legacyが既定。
- Knowledge AI: エントリ・検索系はあるが、本格RAGと引用制御は未完了。
- Proposal Intelligence / Copilot: UI・パネル・一部APIはあるが統合体験は未完了。

## UIのみ

- V80 Prompt BuilderのAutosave体験。
- V80 Story確認、Slide Outline、3ペイン編集。
- AI編集の比較表示とUndo / Redo概念。
- Presentation Quality Scoreの一部表示。

## APIのみ

- Strategy Engine CLI/adapter/evaluator/benchmark/comparison。
- Sales Assistant Proposal Preview / Export。
- 一部Knowledge、Learning、Prompt Experiment、Orchestrator API。

## 設計のみ

- Premium Presentation prototype群。
- Presentation Pack Architecture。
- Proposal Strategy Engineの上位設計。
- Knowledge AIの本格RAG。
- Job型生成、共同編集、Brand Kit永続管理。

## 未実装

- URL単位のProposal Studioルーティング。
- PPTXとHTML previewの完全差分同期。
- SlideElement単位のDB保存。
- 長時間生成Job、Job再試行、キャンセル。
- ブランドロゴアップロードと安全なSVG処理。
- 本格Visual Regression。
- SaaS向け課金、契約、テナント管理。

## 技術的負債

- AppShellが依然として巨大。
- UI状態が`useState`と`localStorage`に分散。
- Versionごとの機能名が多数併存し、ユーザー体験が重複しやすい。
- docsが豊富だが、最新実装との対応表が不足。
- DB schemaは成長しているが、Proposal Studio用の正規化モデルは未整備。
- 同期API中心で、生成処理の進捗・取消・再試行に弱い。

## 重複機能

- Dashboard、Proposal Agent、Copilot、Intelligence、Guided Flowが類似情報を表示。
- Presentation Review、Proposal Optimization、AI編集提案が役割重複。
- Business Improvement、Usage Dashboard、Admin Observabilityで指標が分散。

## 責務が曖昧な機能

- Proposal Agent: 営業支援、KPI、Dashboard、Memoryが混在。
- Proposal Experience Studio: Prompt Builder、Story、Editor、Designerを1コンポーネントで保持。
- Knowledge: Best Practices、Templates、Searchの境界が曖昧。

## 今後の変更リスク

- AppShell分割時に既存E2EとBeautiful.ai導線へ影響が出やすい。
- DB migration追加時にSQLite / PostgreSQL差異が出る可能性がある。
- Strategy v1を既定化する際、Legacy出力との互換性確認が必要。
- PPTX品質改善は出力内容の意味変更を避ける必要がある。

