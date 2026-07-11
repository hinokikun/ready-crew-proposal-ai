# SECURITY

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
- `BEAUTIFUL_AI_API_KEY` must be configured only in Render secrets, never in Vercel or `NEXT_PUBLIC_*` variables.
- The app stores Beautiful.ai presentation IDs and returned editor/player URLs only.
- The app does not store Authorization headers, Beautiful.ai tokens, full case emails, full generated proposal text, or API keys.
- If Beautiful.ai fails, users can continue with the existing PPTX/PDF outputs.
