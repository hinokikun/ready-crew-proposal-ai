# SECURITY

## Version 23.1 Login Mode Security

- ログイン画面は「利用者ログイン」と「管理者ログイン」に分かれています。
- Backendの `/api/auth/login` は任意の `login_mode` を受け取り、ロールと入口の一致を確認します。
- `login_mode` 未指定の既存クライアントは従来互換でログインできます。
- `admin` / `manager` は管理者ログイン、`member` / `viewer` は利用者ログインを使用します。
- 入口不一致、無効ユーザー、ログイン失敗、レート制限は監査ログへ保存します。
- 監査ログにはパスワード、トークン、APIキー、Authorization、メールアドレス全文を保存しません。

## 保存しない情報

以下はDB、Analytics、監査ログ、Knowledge、Release Notes、Integration設定に保存しません。

- OpenAI APIキー
- OAuth token / refresh token
- パスワード
- `DATABASE_URL` 全文
- 案件メール本文全文
- 生成本文全文
- 顧客の機密情報
- 住所、電話番号、メールアドレスなどの個人情報

## 保存してよい情報

業務改善と運用確認に必要な最小限の情報だけ保存します。

- 要約
- メタ情報
- ロール
- 操作ログ
- 監査ログ
- Prompt本文
- 匿名化されたAnalytics指標
- Knowledgeのタグ、評価、ステータス

## 外部連携

現時点では実OAuth接続は実装していません。外部入力は要約とメタ情報のみ保存し、初期状態は `pending_review` です。承認後にのみ案件化できます。

保存禁止:

- OAuth token
- API key
- メール本文全文
- 添付ファイル本体
- パスワード

## 監査ログ

ログイン、生成、レビュー、品質ゲート、ナレッジ承認、リリース公開、Prompt変更、外部入力承認などを記録します。本文全文や機密情報は監査ログに保存しません。

## 権限

- `viewer`: 閲覧のみ。生成、編集、承認、公開は不可
- `member`: 通常作業のみ。管理者APIは利用不可
- `manager`: レビュー承認、リリース承認、一部管理機能
- `admin`: 全機能

管理者APIはBackend側でも権限確認します。

## 社外提出前

AI作成内容は必ず人が確認してください。金額、納期、会社名、実績表記、法務・契約条件、AI推測ラベルは提出前品質ゲートで確認します。

## 表示してはいけない情報

画面、エラー、ログ、README、リリースノートに以下を表示しないでください。

- APIキー
- DB接続文字列全文
- パスワード
- token
- 顧客本文全文
# RC1 Hardening Notes

## Authentication

- `APP_AUTH_SECRET` is required for production authentication.
- Tokens include `issued_at`, `expires_at`, `role`, and `auth_version`.
- If a user is disabled, Pilot access is removed, or `auth_version` changes, existing tokens are rejected.
- Do not log `Authorization` headers, passwords, API keys, or full tokens.

## Rate Limit

- Login, generation, download, Orchestrator, Learning, Prompt Experiment, and External Intake APIs are protected by backend rate limits.
- HTTP 429 responses include `Retry-After` and `request_id`.
- Current implementation is in-memory for RC1 and is intentionally isolated behind a backend interface so Redis can replace it later.

## Maintenance Mode

- `MAINTENANCE_MODE=true` takes priority over screen-based runtime settings.
- During Maintenance Mode, new proposal generation, PPT/PDF creation, Orchestrator execution, Learning execution, Prompt Experiment creation, and external candidate conversion are blocked by backend HTTP 503.
- Login, health checks, CRM/history viewing, admin screens, and audit log viewing remain available.

## Production Secrets

Never expose or paste:

- `OPENAI_API_KEY`
- `BEAUTIFUL_AI_API_KEY`
- `APP_AUTH_SECRET`
- `DATABASE_URL`
- OAuth tokens
- passwords
- customer confidential text

## Beautiful.ai Integration Security

- Beautiful.ai API calls are made only from the Backend.

## Version 18.2 Organization / Workspace Security

- Backend resolves `scope=workspace|organization|system` from the authenticated user. Frontend scope values are never trusted directly.
- General users are limited to the current workspace. Organization scope is limited to admin/manager. System scope is limited to admin.
- Aggregation APIs must default to `workspace`.
- Audit logs include actor user, actor role, organization, workspace, action, target type, target id, request id, and timestamp. They must not include customer body text, generated proposal text, passwords, tokens, or API keys.
- Workspace-dependent browser storage keys include user id, organization id, and workspace id.
- Auth tokens are currently stored in `localStorage` for the browser app. This is acceptable for pilot/internal use only with HTTPS, short token expiry, and no shared devices. A future production hardening option is an HttpOnly secure cookie.
- `DATABASE_URL`, API keys, OAuth tokens, and passwords must never be displayed in Settings, health responses, logs, CSV, Markdown, screenshots, or release notes.
- `BEAUTIFUL_AI_API_KEY` must be configured only in Render secrets, never in Vercel or `NEXT_PUBLIC_*` variables.
- The app stores Beautiful.ai presentation IDs and returned editor/player URLs only.
- The app does not store Authorization headers, Beautiful.ai tokens, full case emails, full generated proposal text, or API keys.
- If Beautiful.ai fails, users can continue with the existing PPTX/PDF outputs.

## Version 19.1 Presentation Review / Revision Security

- Review results are stored as scores, short evidence summaries, selected actions, sanitized outlines, and metadata only.
- Full slide body text, raw Beautiful.ai response bodies, customer emails, API keys, tokens, and passwords must not be saved.
- `member` can create reviews and draft revisions.
- `manager` and `admin` can approve, reject, and regenerate approved revisions in Beautiful.ai.
- `viewer` can read only.
- All presentation review and revision records are scoped by `organization_id` and `workspace_id`.

## Version 20.0 Proposal Optimization Security

- Proposal Optimization stores backlog metadata, scores, confidence, simulation estimates, and sanitized explanations only.
- Best Practice Library stores reusable patterns only.
- Full proposal text, full case emails, customer confidential information, API keys, passwords, Beautiful.ai tokens, and raw Beautiful.ai responses must not be stored.
- `member` can view and select optimization recommendations.
- `manager` and `admin` can approve optimization recommendations.
- `viewer` can read only.
- All optimization backlog and best practice records are scoped by `organization_id` and `workspace_id`.
- Simulation values are estimates and must be presented as estimates.

## Version 20.1 Evidence Governance Security

- Optimization evidence must use aggregate metadata only.
- Evidence displays must not include customer names, customer emails, proposal body text, or raw generated text.
- Predictions must include `is_estimate`, `sample_size`, `evidence_type`, `calculation_method`, `confidence`, and `requires_human_review`.
- Low-sample recommendations must be marked as `ai_estimate` or `insufficient_data`.
- Best Practice records are AI-usable only after manager/admin approval.
- Invalid Backlog status transitions are rejected by the backend.

## Version 22 Security Notes

Version 22??????????????????????????????????????????????

- `app.db` ?Facade?????????????????????????
- `app.health` ????Health????????API???DATABASE_URL?Beautiful.ai token???????
- Router??? `app.router_registry` ??????????Router? `require_roles` ??????????
- Organization / Workspace ???????????Context / Scope??????????
- CSS??????????????DOM???????????????????
