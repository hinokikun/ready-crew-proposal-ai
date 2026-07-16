# ProposalPilot Final Candidate Export

対象: ProposalPilot / AI営業秘書
作成日: 2026-07-16

## 採用候補

Version 33.0のロゴ候補レビューに基づき、正式採用候補は **Pilot Fold** とします。

Pilot Foldは、ProposalPilotの頭文字であるP、提案情報を整理する折り目、次のアクションへ進む導線を抽象化したシンボルです。小さいサイズでも識別しやすく、アプリ、LP、営業資料、OGP、faviconへ展開しやすい候補です。

## 重要な注意

本ファイル群は「正式採用候補」の書き出しデータです。商標調査、類似ロゴ調査、法務確認、社内承認は未完了です。

正式利用前に、人が以下を確認してください。

- 商標登録済みロゴや既存ブランドとの類似がないこと
- 取引先、営業資料、広告で使用して問題がないこと
- 小サイズ、白抜き、単色、印刷で視認性が保たれること
- フォントライセンスと利用環境に問題がないこと

## 作成ファイル

保存先: `docs/design/brand-assets/final-candidate/`

| ファイル | 用途 |
| --- | --- |
| `ProposalPilot_Logo_PilotFold_Color.svg` | Web、LP、営業資料の標準カラー横組みロゴ |
| `ProposalPilot_Logo_PilotFold_Navy.svg` | 印刷、単色に近い管理資料、濃色を抑えたい場面 |
| `ProposalPilot_Logo_PilotFold_White.svg` | Deep Navyなど濃色背景での白抜き表示 |
| `ProposalPilot_Logo_PilotFold_Monochrome.svg` | 白黒印刷、FAX、低彩度資料 |
| `ProposalPilot_Symbol_PilotFold_Color.svg` | アプリ内シンボル、アイコン原稿、SNSアイコン原稿 |
| `ProposalPilot_Symbol_PilotFold_Navy.svg` | 単色寄りのシンボル、管理資料 |
| `ProposalPilot_Logo_PilotFold_Color.png` | PowerPoint、Word、非デザイナー向け編集資料 |
| `ProposalPilot_Symbol_512.png` | アプリアイコン、ストア、社内ポータル用マスター |
| `ProposalPilot_Symbol_192.png` | PWA、Android、Web App Manifest用 |
| `ProposalPilot_AppleTouchIcon_180.png` | Apple touch icon用 |
| `ProposalPilot_Favicon_48.png` | favicon高解像度候補 |
| `ProposalPilot_Favicon_32.png` | favicon標準候補 |
| `ProposalPilot_Favicon_16.png` | favicon最小候補 |
| `favicon.ico` | 16 / 32 / 48 pxを含むICO候補 |
| `ProposalPilot_OGP_1200x630.png` | OGP、SNSシェア、製品紹介リンク用 |

## 推奨最小サイズ

| 用途 | 推奨最小サイズ |
| --- | --- |
| 横組みロゴ | 幅160px以上 |
| シンボル | 24px以上 |
| favicon | 16px以上 |
| OGP | 1200x630px固定 |
| 印刷資料 | 横組みロゴ幅30mm以上 |

## 背景別の利用方法

- 白背景: `ProposalPilot_Logo_PilotFold_Color.svg`
- 淡色背景: `ProposalPilot_Logo_PilotFold_Color.svg`
- Deep Navy背景: `ProposalPilot_Logo_PilotFold_White.svg`
- 白黒印刷: `ProposalPilot_Logo_PilotFold_Monochrome.svg`
- 小サイズUI: `ProposalPilot_Symbol_PilotFold_Color.svg`

## favicon / App Icon

favicon候補は、Pilot Foldのシンボル単体を使用します。小サイズで文字は読めないため、ロゴタイプではなくシンボルのみを使用してください。

App Iconは `ProposalPilot_Symbol_512.png` をマスターとして、必要サイズへ縮小する想定です。

## OGP

OGP候補は1200x630pxです。CTA、会社名、URL、電話番号、実顧客情報は含めていません。公開URLや問い合わせ先が確定した後でも、OGPには過度な情報を詰め込まず、製品名と主要コピーを中心にしてください。

## SVG安全性

今回作成したSVGは以下の方針で書き出しています。

- scriptなし
- 外部参照なし
- embedded raster imageなし
- 不要なmetadataなし
- viewBoxあり
- ブランドカラーのみ使用

## フォント注意事項

SVGは表示環境により代替フォントで表示される場合があります。最終入稿・広告・商用配布の前には、必要に応じてアウトライン化した版をデザイナーが作成してください。

推奨フォント:

- 英字: Inter / Segoe UI / Arial
- 日本語: Noto Sans JP / Yu Gothic / Meiryo

## 正式利用前チェック

- [ ] 商標調査を完了した
- [ ] 類似ロゴ調査を完了した
- [ ] 社内承認を完了した
- [ ] 小サイズ表示を確認した
- [ ] 白抜き表示を確認した
- [ ] 印刷資料で確認した
- [ ] faviconを実ブラウザで確認した
- [ ] OGPを実URLで確認した
