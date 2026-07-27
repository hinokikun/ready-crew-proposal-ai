# AI営業秘書 / Ready Crew Proposal AI

AI営業秘書は、案件情報の整理から提案書作成、提出前確認、PowerPoint / PDF / Beautiful.ai出力、履歴管理、監査ログまでを一つの画面で扱う営業支援アプリケーションです。

Version 1.0は、社内利用・限定顧客提供・受託提案支援を想定した正式リリース候補です。新しい営業AIを増やすのではなく、既存の提案生成、Quality Gate、Beautiful.ai、作成履歴、権限管理、監査ログを安定運用できる状態へ整理しています。

## Version 80: Proposal Experience Edition

Version 80では、既存の提案生成、PowerPoint、PDF、Beautiful.ai、Quality Gateを維持したまま、提案作成体験を整理しました。

- 固定サイドバーによるアプリケーション型ナビゲーション
- モバイル向けドロワーメニュー
- ステップ形式のPrompt Builder
- 不足情報を最大3件で案内するSmart Prompt Builder
- 提案ストーリーとスライド構成を確認するStory Engine
- スライド一覧、プレビュー、AI改善提案を並べる3ペイン編集
- PowerPoint向けPresentation Designer
- 8種類のPPTテンプレート選択
- 100点満点のPPT品質チェック

詳細は [docs/design/proposal-experience-v80/overview.md](docs/design/proposal-experience-v80/overview.md) を参照してください。

## Version 81: AI Sales Secretary Product Planning Pack

Version 81以降の開発基準として、現在の実装状態と将来構想を分離したProduct Planning Packを追加しました。

- [AI営業秘書 Product Planning Pack](docs/product-planning/v81/README.md)
- 実装済み、部分実装、設計のみ、未実装を区別
- Proposal Studio、Prompt Builder、Story Engine、Presentation AI Engine、PPT品質基準、Version 81〜90ロードマップを整理

## 特徴

- 案件メール、議事録、ヒアリングメモから提案書の初稿を作成
- 一般利用者向けの7ステップ「かんたん操作フロー」
- 提出前チェックで、社外提出前の人間確認を必須化
- 要約PowerPoint、詳細PowerPoint、見積PDFを出力
- Beautiful.ai Prompt APIと連携し、デザイン済みプレゼンを生成
- Presentation ReviewとProposal Optimizationで提案書改善を支援
- Organization / Workspace単位でデータを分離
- admin / manager / member / viewerの権限管理
- 作成履歴、監査ログ、Beautiful.ai診断、Maintenance Modeを搭載
- ProposalPilot Design Systemに基づくBtoB SaaS UI

## デザインシステム

Version 28.0から、ProposalPilot / AI営業秘書の画面品質を揃えるためのデザインシステムを追加しています。

- [Design System概要](docs/design-system/README.md)
- [Design Tokens](docs/design-system/DESIGN_TOKENS.md)
- [Components](docs/design-system/COMPONENTS.md)
- [Layout](docs/design-system/LAYOUT.md)
- [Accessibility](docs/design-system/ACCESSIBILITY.md)
- [Responsive](docs/design-system/RESPONSIVE.md)
- [Migration Guide](docs/design-system/MIGRATION_GUIDE.md)

## 主な機能

### 利用者向け

- ログイン
- 案件情報入力
- AI提案書作成
- 提案内容確認
- 提出前チェック
- PowerPoint / PDF出力
- Beautiful.ai出力
- AIレビューと改善
- 作成履歴
- Workspace切替
- 通知確認

### 管理者向け

- ユーザー管理
- Organization / Workspace管理
- Role管理
- 監査ログ
- Product Analytics
- Beautiful.ai診断
- AI営業アシスタント（Feature Flag有効時、DB保存なし）
- Maintenance Mode
- UAT確認
- Release / Operations文書確認

## 技術構成

- Frontend: Next.js / React / Vercel
- Backend: FastAPI / Render
- Database: SQLite対応、PostgreSQL移行準備済み
- AI: OpenAI API、Mock AI mode
- Presentation: PPTX / PDF / Beautiful.ai Prompt API
- Test: pytest / Playwright

## 導入方法

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env.local
npm.cmd run dev
```

## 環境変数

### Backend / Render

| 変数 | 用途 |
| --- | --- |
| `APP_ENV` | `production` / `local` など |
| `APP_AUTH_SECRET` | 認証トークン署名用Secret |
| `INITIAL_ADMIN_EMAIL` | 初期管理者メール |
| `INITIAL_ADMIN_PASSWORD` | 初期管理者パスワード |
| `DATABASE_URL` | SQLiteまたはPostgreSQL接続先 |
| `CORS_ORIGINS` | Vercel本番URLをカンマ区切りで指定 |
| `OPENAI_API_KEY` | OpenAI APIキー |
| `USE_MOCK_AI` | Mock AI利用時は `true` |
| `BEAUTIFUL_AI_ENABLED` | Beautiful.ai連携を有効化 |
| `BEAUTIFUL_AI_API_KEY` | Beautiful.ai APIキー |
| `BEAUTIFUL_AI_API_MODE` | 既定は `prompt` |
| `BEAUTIFUL_AI_BASE_URL` | `https://beautiful.ai/api/v1` |
| `BEAUTIFUL_AI_DEFAULT_THEME_ID` | Beautiful.ai theme ID |
| `SALES_ASSISTANT_ENABLED` | AI営業アシスタントAPIを有効化。既定は `false` |
| `SALES_ASSISTANT_PROPOSAL_ENABLED` | AI営業アシスタントからProposal Preview生成を有効化。既定は `false` |
| `PROPOSAL_EXPORT_ENABLED` | Proposal PreviewからPowerPoint / Beautiful.ai Exportを有効化。既定は `false` |
| `MAINTENANCE_MODE` | メンテナンス停止 |

### Frontend / Vercel

| 変数 | 用途 |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Render Backend URL |
| `NEXT_PUBLIC_APP_VERSION` | Frontend表示用Version |
| `NEXT_PUBLIC_GIT_COMMIT` | Build commit表示 |
| `NEXT_PUBLIC_BUILD_TIME` | Build time表示 |
| `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED` | AI営業アシスタント管理UIの表示。既定は `false` |
| `NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED` | Proposal Export UIの表示補助。Backend flagが最終判定 |

APIキー、Password、Token、DATABASE_URLの実値はコード、README、ログ、スクリーンショットへ記録しないでください。

### 初期管理者の自動作成

Backend起動時に `INITIAL_ADMIN_EMAIL` と `INITIAL_ADMIN_PASSWORD` が設定されている場合、同じメールアドレスのユーザーがDBに存在しないときだけ `admin` ロールの初期管理者を作成します。既にユーザーが存在する場合、パスワードやRoleは上書きしません。

Renderでは Environment に次を設定してからBackendを再デプロイしてください。

- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `APP_AUTH_SECRET`
- `DATABASE_URL`

`INITIAL_ADMIN_PASSWORD` には本番用の強いパスワードを設定し、ログやスクリーンショットへ表示しないでください。起動ログにはメールアドレスを伏せた作成結果だけが出力されます。

Renderの通常ファイルシステム上にSQLite DBを置くと、デプロイや再起動でDBが失われる可能性があります。本番運用ではRender PostgreSQLを `DATABASE_URL` に設定するか、SQLiteを使う場合は永続ディスク上のパスを指定してください。

## Feature Flag一覧

| 名称 | デフォルト | 対象画面 | 対象API | 管理者限定 | 依存関係 |
| --- | --- | --- | --- | --- | --- |
| `USE_MOCK_AI` | `false` | Proposal生成結果 | `/api/analyze` と既存Proposal Generator | いいえ | 本番では原則 `false` |
| `MAINTENANCE_MODE` | `false` | 生成・出力系UI | 生成・出力系API | いいえ | 障害時に新規操作を停止 |
| `PILOT_MODE` | `false` | Pilot関連UI | Pilot制御 | 管理者操作のみ | `PILOT_MAX_USERS` など |
| `BEAUTIFUL_AI_ENABLED` | `false` | Beautiful.ai出力・診断 | `/api/beautiful-ai/*` | 診断は管理者限定 | APIキー設定が必要 |
| `BEAUTIFUL_AI_MOCK` | `false` | Beautiful.ai診断 | `/api/beautiful-ai/*` | 診断は管理者限定 | 本番実生成とは別扱い |
| `BEAUTIFUL_AI_API_MODE` | `prompt` | Beautiful.ai診断 | Beautiful.ai生成 | 診断は管理者限定 | `prompt` / `structured` |
| `PRESENTATION_ENGINE_MODE` | `legacy` | PPTX生成影響範囲 | Presentation Context連携境界 | いいえ | `legacy` が既定 |
| `SALES_ASSISTANT_ENABLED` | `false` | AI Sales Assistant管理画面 | `/api/sales-assistant/generate` | はい | `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED` |
| `SALES_ASSISTANT_PROPOSAL_ENABLED` | `false` | Proposal Previewカード | `/api/sales-assistant/proposal-preview` | はい | `SALES_ASSISTANT_ENABLED=true` |
| `PROPOSAL_EXPORT_ENABLED` | `false` | Human Review & Exportカード | `/api/sales-assistant/export` | はい | `SALES_ASSISTANT_ENABLED=true`, `SALES_ASSISTANT_PROPOSAL_ENABLED=true` |
| `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED` | `false` | 管理コンソール内AI Sales Assistant | なし | UI表示のみ | Backend flagも必要 |
| `NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED` | `false` | Proposal Export UI表示補助 | なし | UI表示のみ | Backend flagが最終判定 |

Version53時点では、Sales AssistantからPPTX / Beautiful.ai ExportへFeature Flag付きで接続できます。DB保存、メール、学習、ダッシュボードへは接続していません。

## Version52 Readiness Notes

- API互換: Version41 Strategy Brief、Version49 Sales Assistant Brief、Version50 UI、Version51 Proposal Previewの主要キーを維持しています。
- Security Review: 管理者限定API、Feature Flag OFF、巨大入力、JSON不正、内部例外、Proposal失敗の安全なエラーを確認しています。ログ・例外へPassword、Token、APIキー実値を出さない方針です。
- Performance Review: Mock AI / TestClient / 5回平均で、Sales Assistant生成は約10.08ms、Proposal Preview生成は約18.04ms、巨大入力拒否は約5.06msでした。外部OpenAI利用時は別途本番環境で測定してください。
- Monitoring設計: APIエラー率、Human Review件数、Feature Flag利用率、Proposal Preview生成数、Fallback率を将来監視対象にします。

## Version55 Maintainability Notes

- Version55では新機能、DB、Migration、PPTX生成、Beautiful.ai生成、Proposal Generatorを変更せず、保守性レビューとテストfixture整理だけを行っています。
- Logging方針、依存関係、Architecture Cleanup、Release Assessmentは [docs/release/v55/README.md](docs/release/v55/README.md) を確認してください。
- Feature Flagの最終判定はBackendで行います。Frontendの公開環境変数は表示補助であり、権限やExport可否の根拠にはしません。

## 管理者ガイド

1. 管理者ログインからログインします。
2. ユーザー管理でmember / viewerを作成します。
3. Organization / Workspaceを確認します。
4. Beautiful.ai診断で接続状態を確認します。
5. 監査ログでログイン、生成、出力、設定変更を確認します。
6. 重大障害時はMaintenance Modeを有効化します。
7. AI営業アシスタントを検証する場合は、Backend / Frontend両方のFeature Flagを有効にし、管理コンソール内の「AI Sales Assistant / AI営業アシスタント」から確認します。Proposal Preview連携は `SALES_ASSISTANT_PROPOSAL_ENABLED=true`、Export連携は `PROPOSAL_EXPORT_ENABLED=true` の場合のみ使えます。
8. 本番公開前は `docs/PRODUCTION_CHECKLIST.md` と `docs/V1_0_RELEASE_NOTES.md` を確認します。

## 利用者ガイド

1. 利用者ログインからログインします。
2. STEP 1で案件情報を貼り付けます。
3. STEP 2でAI提案書を作成します。
4. STEP 3で内容を確認します。
5. STEP 4で提出前チェックを完了します。
6. STEP 5で要約PPTX、詳細PPTX、見積PDF、Beautiful.aiを選びます。
7. STEP 6でAIレビューと改善を確認します。
8. STEP 7で案件を完了します。

## 研修提出版の使い方

作成履歴画面の「業務改善ダッシュボード」では、AI営業秘書を実業務で使った結果を研修提出用にまとめられます。

- 測定回数、平均短縮率、平均短縮時間、累計削減時間、品質平均、ミス件数合計をカードで確認できます。
- 短縮率推移、短縮時間、品質推移、ミス件数推移をグラフで確認できます。
- 「研修提出レポートを作成」を押すと、WordやMarkdownへ貼り付けやすい文章を自動作成します。
- 「発表用サマリー作成」を押すと、2〜3分の発表で使える説明文を作成します。
- 「スクリーンショットモード」「ダークモード」「フルスクリーン表示」を使うと、発表資料用の画面キャプチャを取りやすくなります。
- 「サンプルデータ投入」を押すと、研修デモ用の履歴、改善レポート、統計データを数件作成できます。
- 「研修提出CSV」には、測定日、案件名、短縮率、短縮時間、品質、ミス件数が含まれます。

## Version50 Proposal Agent

Version50では、AI営業秘書を「Proposal AI」から「Proposal Agent」へ拡張しました。単に提案書を生成するだけでなく、営業担当者が次に何を確認すべきか、提案品質がどの程度か、どの案件が送付待ちかをトップ画面で確認できます。

- Proposal Agent Dashboardで、提案待ち、提案書作成中、提案完了、見積作成待ち、Beautiful.ai生成待ち、顧客送付待ちをカード表示します。
- Agent ToDoで、ヒアリング不足、予算確認、競合比較、見積確認、スライド生成、顧客送付の次アクションをチェックできます。
- Proposal Scoreで、課題整理、提案内容、競合分析、見積、ストーリー性、確認事項を0〜100点で確認できます。
- Timelineで、案件登録、AI分析、提案生成、Beautiful.ai生成、顧客送付、受注までの流れを確認できます。
- Agent Memoryで、ヒアリング内容、確認事項、提案内容、競合分析、改善履歴を案件ごとに保存できます。
- Proposal Reviewで、改善点、リスク、不足情報を一覧化します。
- Executive Summaryで、経営者向け30秒版、営業向け3分説明版、詳細版を表示します。

## Version60 Proposal Intelligence Platform

Version60では、Proposal Agentを営業活動全体を支援する「Proposal Intelligence Platform」へ拡張しました。提案書作成だけではなく、案件の優先順位、受注確率、案件健康度、競合比較、営業アクション、営業KPI、AI Insightsを同じトップ画面で確認できます。

- Priority Engineで、予算、納期、業種、案件規模、競合状況、過去受注率、提案難易度をもとにA〜Eと星評価で優先順位を表示します。
- 受注確率AIで、Proposal Scoreとは別に案件ごとの受注確率と理由を表示します。
- 競合比較ダッシュボードで、競合の強み、弱み、差別化ポイント、注意点を営業で使いやすいカードとして整理します。
- 営業アクション提案で、電話、メール送信、ヒアリング追加、見積修正、決裁者確認、競合調査などの次アクションを提示します。
- 案件健康度で、Healthy / Warning / Criticalを表示し、注意すべき理由を示します。
- KPI Dashboardで、提案数、提案成功率、平均Proposal Score、平均受注確率、平均作成時間、累計削減時間、Beautiful.ai生成数を確認できます。
- AI Insightsで、最近の傾向や不足しがちな確認事項を表示します。
- ダッシュボードはMarkdown、CSV、PDF、PowerPointで出力できます。

## Version70 Proposal Copilot Enterprise

Version70では、Proposal Intelligence Platformのトップ画面を「Proposal Copilot Enterprise」として刷新しました。営業担当者が初めて触っても、案件入力、提案作成、次アクション、出力状況を迷わず扱えるように、近代的なカードUI、グラス調のレイアウト、ダーク / ライト切替、チャット相談、通知、コマンドパレットを追加しています。

- ホーム画面で、今日やること、優先案件、期限が近い案件、受注確率ランキング、Smart Recommendation、最近使った案件を確認できます。
- 右下のProposal Copilotで、「この案件どう思う？」「競合は？」「受注率を上げるには？」などをチャット形式で相談できます。
- 案件概要からワンクリック提案書フローを開始し、Thinking、Analyzing、Creating Proposal、Beautiful.ai、PDF、PowerPointの進捗をタイムラインで確認できます。
- 業種別テンプレート、5秒ごとの自動保存、Ctrl+Z / Ctrl+Shift+Z、Ctrl+KのCommand Palette、通知センターを利用できます。
- Beautiful.ai生成後のスライド構成プレビュー、最近使った案件、お気に入りPin、営業KPI、競合比較、AIレビュー、Agent Memoryを同じ画面から確認できます。

## Version71 Training Submission Release Candidate

Version71では、社内研修課題の提出・発表に使えるよう、実測データの安全な記録、デモデータ分離、提出用Markdown、発表原稿、利用マニュアル、管理者手順、リリース判定資料を整備しました。新しい大型AI機能は追加していません。

- 業務改善レポートでは、使用前時間、AI入力時間、AI処理待ち時間、内容確認時間、修正時間を分けて記録します。
- 使用後合計時間は、AI入力時間＋AI処理待ち時間＋確認時間＋修正時間として自動計算します。
- 短縮時間は「使用前時間−使用後合計時間」、短縮率は「短縮時間÷使用前時間×100」で計算します。
- デモモードで作成したデータは「デモデータ」として識別し、通常のKPI、CSV、研修提出レポート、発表用サマリーには含めません。
- 「デモデータも表示」を選んだ場合だけ、画面上でサンプルを確認できます。提出時は実データのみを使用してください。
- 提出用チェックリスト、提出Markdownテンプレート、発表原稿、利用マニュアル、管理者運用手順は `docs/training-submission/` にあります。
- 本番反映前には、`20260722_2500_training_metrics.py`、`20260722_5000_proposal_agent_memory.py`、`20260722_7100_training_submission_rc.py` の順でmigrationが適用できることを確認してください。

## テスト

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

共通:

```powershell
git diff --check
```

## FAQ

### Beautiful.aiボタンが押せません

提案書作成、提出前チェック、Beautiful.ai設定、権限、Maintenance Modeを確認してください。管理者はBeautiful.ai診断情報も確認できます。

### PowerPointやPDFが出ません

通信エラー、入力不足、Maintenance Mode、Backendエラーの可能性があります。画面のrequest_idを管理者へ共有してください。

### 管理者メニューが見えません

member / viewerには管理者メニューは表示されません。管理者機能が必要な場合はadminに相談してください。

### 実顧客情報を入力してよいですか

正式運用ルールに従ってください。UATやデモでは架空データのみ使用してください。Password、APIキー、Tokenは入力禁止です。

### Cloudで動かない場合は何を見ますか

GitHub Actions、Vercel Deployment、Render Deploy、`/health`、`/health/ready`、Beautiful.ai診断を確認します。

## ドキュメント

- [Version 1.0 Release Notes](docs/V1_0_RELEASE_NOTES.md)
- [User Manual](docs/USER_MANUAL_TEXT.md)
- [Admin Manual](docs/ADMIN_MANUAL_TEXT.md)
- [Role Permissions](docs/ROLE_PERMISSIONS.md)
- [Security](SECURITY.md)
- [Support](SUPPORT.md)
- [Operations](docs/OPERATIONS.md)
- [Release](docs/RELEASE.md)
- [Backup / Restore](docs/BACKUP_RESTORE.md)
- [Production Checklist](docs/PRODUCTION_CHECKLIST.md)
- [Demo Data](docs/DEMO_DATA.md)
- [AI Sales Assistant v50](docs/design/proposal-sales-assistant/v50/README.md)
- [AI Sales Assistant Proposal Integration v51](docs/design/proposal-sales-assistant/v51/README.md)
- [Archive](docs/archive/README.md)

## License

MIT License. See [LICENSE](LICENSE).
