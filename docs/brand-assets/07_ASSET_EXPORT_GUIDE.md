# ProposalPilot ブランド資産書き出しガイド

対象: ProposalPilot / AI営業秘書

## 1. マスターファイル

| 資産 | マスターファイル |
| --- | --- |
| ロゴ候補 | `docs/design/brand-assets/ProposalPilot_Logo_Concepts_v1.pptx` |
| ブランド資産一覧 | `docs/design/brand-assets/ProposalPilot_Brand_Assets_v1.pptx` |
| SVG候補 | `docs/design/brand-assets/svg/` |
| 利用ルール | `docs/brand-assets/` |

## 2. 推奨書き出し形式

| 用途 | 形式 |
| --- | --- |
| 編集用 | PPTX |
| 確認用 | PDF |
| Web掲載 | PNG / SVG |
| 印刷 | PDF / SVG |
| favicon | ICO / PNG |
| アプリアイコン | PNG |
| OGP | PNG |
| SNS | PNG |

## 3. ロゴ書き出し

候補ごとに以下を用意します。

- 横組みロゴ
- 縦組みロゴ
- シンボル単体
- カラー版
- Deep Navy版
- 白抜き版
- モノクロ版

命名例:

- `ProposalPilot_Logo_A_Horizontal_Color`
- `ProposalPilot_Logo_A_Symbol_Color`
- `ProposalPilot_Logo_A_Symbol_Mono`
- `ProposalPilot_Logo_A_White`

## 4. SVG書き出しルール

- テキストは可能な限り編集可能に保つ
- 外部参照を含めない
- scriptを含めない
- 不要なmetadataを含めない
- viewBoxを設定する
- 塗り色はブランドカラーを使用

## 5. PNG書き出しルール

- 透過が必要な場合はPNG
- 背景あり版と背景なし版を分ける
- OGPは1200x630
- SNSは1200x675
- YouTubeは1280x720
- App Iconは512x512を基準に縮小する

## 6. PDF書き出しルール

- 文字切れなし
- 空白ページなし
- 画像の粗さなし
- A4や16:9での見え方を確認
- 印刷時の余白を確認

## 7. 使用先別の推奨

| 使用先 | 推奨資産 |
| --- | --- |
| アプリ | シンボル単体、横組みロゴ |
| LP | 横組みロゴ、OGP画像 |
| パンフレット | 横組みロゴ、白抜き版 |
| 製品カタログ | 横組みロゴ、カラー版 |
| 営業デモ資料 | 横組みロゴ、シンボル単体 |
| GitHub README | 横組みロゴ、OGP |
| SNS | OGP / SNSテンプレート |
| 展示会 | 縦組みロゴ、白抜き版 |
| 名刺 | 横組みロゴ、モノクロ版 |

## 8. 公開前確認

- [ ] 実顧客情報なし
- [ ] 秘密情報なし
- [ ] 商標登録済みと誤認される表記なし
- [ ] 外部有料素材の無断使用なし
- [ ] 会社情報未確定部分は要入力
- [ ] QRコード未確定部分は要差替え
- [ ] ファイル名が用途と一致している
- [ ] 最新マスターファイルから書き出している
