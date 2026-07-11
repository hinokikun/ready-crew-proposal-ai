# Beautiful.ai 連携

AI営業秘書で作成した提案内容を、Beautiful.ai の公式APIへ渡してデザイン済みプレゼンテーションを作成する追加出力です。既存の要約PPT、詳細PPT、見積PDFは引き続き利用できます。

## 利用条件

- Backendのみが Beautiful.ai API を呼び出します。
- Frontendへ `BEAUTIFUL_AI_API_KEY` は渡しません。
- 提出前品質ゲートが完了している案件だけ作成できます。
- Maintenance Mode中は新規作成できません。
- viewer は閲覧のみで、Beautiful.ai作成はできません。

## 環境変数

Render Backend に設定します。Vercel Frontend には設定しません。

```env
BEAUTIFUL_AI_ENABLED=false
BEAUTIFUL_AI_API_KEY=
BEAUTIFUL_AI_BASE_URL=https://www.beautiful.ai/api/v1
BEAUTIFUL_AI_DEFAULT_THEME_ID=
BEAUTIFUL_AI_TIMEOUT_SECONDS=120
BEAUTIFUL_AI_MOCK=false
```

任意:

```env
BEAUTIFUL_AI_WORKSPACE_ID=
BEAUTIFUL_AI_FOLDER_ID=
BEAUTIFUL_AI_IMAGE_SOURCE=ai
BEAUTIFUL_AI_IMAGE_STYLE=clean corporate proposal
```

## モックモード

社内検証では次の設定で、実Beautiful.ai APIを呼ばずに安全に動作確認できます。

```env
BEAUTIFUL_AI_ENABLED=true
BEAUTIFUL_AI_MOCK=true
```

モックモードでは `https://www.beautiful.ai/editor/mock-...` のようなテストURLを返します。

## API

- `GET /api/beautiful-ai/status`
- `POST /api/beautiful-ai/presentations`
- `GET /api/beautiful-ai/presentations/{project_id}`
- `POST /api/beautiful-ai/presentations/{presentation_id}/editor-opened`

作成APIは `Authorization: Bearer ...` のアプリログイントークンが必要です。Beautiful.ai APIキーはBackend内部でのみ利用します。

## Beautiful.aiへ送る内容

既存の `powerpoint_generation_data` から、以下のようなスライド情報へ変換します。

- `title`
- `body`
- `content`
- `presenterNotes`
- `layoutHint`
- `imagePrompt`
- `sourceLabel`

`language: "ja"` と `preserveExactText: true` を付与し、社名、金額、納期、URL、実績数値、契約条件などの書き換えを避けます。未確定項目は「要確認」として扱います。

## 保存する情報

`beautiful_ai_presentations` に以下のみ保存します。

- 案件ID
- ユーザーID
- Beautiful.ai presentation ID
- タイトル
- editor URL / player URL
- ステータス
- theme ID
- 短いリクエスト要約
- エラー種別

保存しないもの:

- Beautiful.ai APIキー
- Authorizationヘッダー
- 案件メール全文
- 生成本文全文
- 個人情報
- Beautiful.ai token

## エラー時の扱い

Beautiful.aiが利用できない場合も、既存PPTX/PDF出力は利用できます。

- 401: Beautiful.ai APIキーを確認してください
- 403: Beautiful.ai APIの利用権限が有効になっていません
- 429: Beautiful.aiの利用上限に達しました。時間を置くか既存PPTXをご利用ください
- timeout: Beautiful.aiの処理に時間がかかっています。既存PPTXも利用できます
- disabled: Beautiful.ai連携は未設定です。既存PPTXをご利用ください

## 公式APIについて

初期実装は `POST {BEAUTIFUL_AI_BASE_URL}/createPresentation` を呼び出します。Beautiful.ai側の契約プランやAPI仕様により、エンドポイント名・レスポンス項目が異なる場合は `BEAUTIFUL_AI_BASE_URL` またはサービス層を調整してください。ブラウザ自動操作や非公式APIは利用しません。
