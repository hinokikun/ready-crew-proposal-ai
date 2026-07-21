# Download Contract

## Endpoint

`POST /api/sales-assistant/export/download`

## Request

`POST /api/sales-assistant/export`と同じExport payloadを送信する。

必須条件:

- `export_type`は`powerpoint`
- `PROPOSAL_EXPORT_ENABLED=true`
- admin認証済み
- Human Review条件を満たす

## Response

成功時:

- HTTP 200
- `Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation`
- `Content-Disposition: attachment; filename="ProposalPilot_proposal.pptx"; filename*=UTF-8''...`
- `Cache-Control: no-store`

失敗時:

- JSON error
- `error_type`
- 安全な`message`

## Filename

形式:

`ProposalPilot_<案件名>_<YYYYMMDD-HHmm>.pptx`

安全化ルール:

- path separatorを除去する
- control characterを除去する
- 長すぎる名前を短縮する
- 日本語は可能な限り維持する
- 不明な場合は`proposal`へfallbackする

## Integrity Check

返却前に以下を確認する。

- 0 byteではない
- ZIPとして開ける
- `[Content_Types].xml`が存在する
- `ppt/presentation.xml`が存在する
- slide xmlが1件以上存在する
- python-pptxで再オープンできる
- slide数が1以上
