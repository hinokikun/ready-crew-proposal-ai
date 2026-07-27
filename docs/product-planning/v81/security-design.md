# Security Design

## Implemented Controls

- Authentication: JWT login/status/logout。
- Authorization: role checks、admin/manager/member/viewer。
- Workspace / Organization isolation: contextとテストあり。
- Password: hash保存。
- Secret: APIキー値をレスポンスに返さない。
- Beautiful.ai: Authorizationログ禁止、URL自前生成禁止方針。
- Audit Log: login、生成、管理操作の一部。
- Rate Limit: generation/admin系。

## Future Controls

- Object Level Authorization for Proposal, ProposalVersion, ExportArtifact.
- Signed URL for artifacts.
- File upload validation for Brand Kit and Knowledge.
- CSV injection sanitization for every export.
- Markdown/HTML sanitization for AI output.
- Prompt Injection and Indirect Prompt Injection guard.
- AI output schema validation.
- Input size limit per field and per job.
- Admin operation dual control for destructive actions.
- Incident response playbook and secret rotation runbook.

## Logging Rules

ログへ出してはいけないもの: password, API key, token, Authorization, Cookie, DB URL, 顧客本文全文、個人情報の過剰表示。

