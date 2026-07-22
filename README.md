# AI営業秘書 / Ready Crew Proposal AI

AI営業秘書は、案件情報の整理から提案書作成、提出前確認、PowerPoint / PDF / Beautiful.ai出力、履歴管理、監査ログまでを一つの画面で扱う営業支援アプリケーションです。

Version 1.0は、社内利用・限定顧客提供・受託提案支援を想定した正式リリース候補です。新しい営業AIを増やすのではなく、既存の提案生成、Quality Gate、Beautiful.ai、作成履歴、権限管理、監査ログを安定運用できる状態へ整理しています。

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
