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
| `MAINTENANCE_MODE` | メンテナンス停止 |

### Frontend / Vercel

| 変数 | 用途 |
| --- | --- |
| `NEXT_PUBLIC_API_URL` | Render Backend URL |
| `NEXT_PUBLIC_APP_VERSION` | Frontend表示用Version |
| `NEXT_PUBLIC_GIT_COMMIT` | Build commit表示 |
| `NEXT_PUBLIC_BUILD_TIME` | Build time表示 |

APIキー、Password、Token、DATABASE_URLの実値はコード、README、ログ、スクリーンショットへ記録しないでください。

## 管理者ガイド

1. 管理者ログインからログインします。
2. ユーザー管理でmember / viewerを作成します。
3. Organization / Workspaceを確認します。
4. Beautiful.ai診断で接続状態を確認します。
5. 監査ログでログイン、生成、出力、設定変更を確認します。
6. 重大障害時はMaintenance Modeを有効化します。
7. 本番公開前は `docs/PRODUCTION_CHECKLIST.md` と `docs/V1_0_RELEASE_NOTES.md` を確認します。

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
- [Archive](docs/archive/README.md)

## License

MIT License. See [LICENSE](LICENSE).
