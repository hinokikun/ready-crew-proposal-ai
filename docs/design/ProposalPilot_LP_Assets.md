# ProposalPilot LP Assets

対象ファイル:

- `ProposalPilot_LP_v1.html`
- `ProposalPilot_LP_v1.pdf`
- `ProposalPilot_LP_v1.fig.md`
- `ProposalPilot_LP_Copy.md`

## 1. 制作概要

| 項目 | 内容 |
|---|---|
| ブランド名 | ProposalPilot |
| 製品名 | AI営業秘書 |
| Tagline | Accelerate Every Proposal. |
| メインコピー | 営業提案をAIでもっと速く、もっと美しく。 |
| 目的 | 公式製品紹介LPの販促用静的HTML/PDF |
| 実装範囲 | `docs/design` 配下の販促物のみ |

## 2. 参照したブランド資料

- `docs/brand/01_BRAND_GUIDE.md`
- `docs/brand/02_VISUAL_GUIDE.md`
- `docs/brand/03_PRODUCT_POSITIONING.md`
- `docs/brand/04_MESSAGING.md`
- `docs/brand/09_CLAIMS_AND_EVIDENCE.md`
- `docs/brand/12_LP_CONTENT_SOURCE.md`
- `docs/brand/14_ASSET_AND_SCREENSHOT_LIST.md`
- `docs/DEMO_DATA.md`

## 3. ブランドカラー

| 用途 | 色名 | Hex |
|---|---|---|
| Primary | Proposal Blue | `#155EEF` |
| Dark | Deep Navy | `#102A43` |
| Accent | Cyan | `#2DE2E6` |
| Success | Emerald | `#12B76A` |
| Background | Background | `#F8FAFC` |
| Surface | Surface | `#FFFFFF` |
| Text | Text Primary | `#1D2939` |
| Muted | Text Secondary | `#667085` |
| Border | Border | `#E4E7EC` |

## 4. フォント

| 用途 | 指定 |
|---|---|
| 日本語 | Noto Sans JP |
| 英字 | Inter |
| Fallback | Segoe UI, system-ui, sans-serif |

## 5. 使用素材

外部画像ファイルは使用していません。HTML内のCSS、図形的なレイアウト、疑似UIモックで構成しています。

| 素材 | 種別 | 用途 | 備考 |
|---|---|---|---|
| ProposalPilotマーク | CSS図形 | ナビ、Footer、Hero | 正式ロゴ確定後に差し替え可能 |
| Hero UIモック | HTML/CSS | ファーストビュー背景 | 実スクリーンショットではありません |
| 7ステップUI | HTML/CSS | Hero、利用フロー | ガイドUIの概念表現 |
| スクリーンショットカード | HTML/CSS | 主要画面紹介 | 架空データの画面モック |
| 機能アイコン | テキスト + CSS | 機能一覧 | 外部アイコン未使用 |
| FAQ | HTML details | FAQ表示 | JavaScript未使用 |

## 6. スクリーンショット差し替え候補

正式公開時には、以下を実画面スクリーンショットへ差し替えできます。

- ホーム
- 案件入力
- 提案生成
- 提出前チェック
- 出力
- 管理画面

撮影時は `docs/brand/14_ASSET_AND_SCREENSHOT_LIST.md` のマスキングルールに従ってください。

## 7. 未確定・差し替え項目

- 正式ロゴ
- 正式ブランドマーク
- 製品サイトURL
- 問い合わせフォームURL
- 製品資料ダウンロードURL
- 会社名
- 住所
- 利用規約URL
- プライバシーポリシーURL
- 料金
- サポート範囲
- 実画面スクリーンショット

## 8. 安全確認

- 実顧客名、実メールアドレス、実電話番号は掲載していません。
- APIキー、Password、Token、Authorization、DATABASE_URL、request_idは掲載していません。
- 未検証の効果数値、受注率向上、作業時間削減率は掲載していません。
- 「完全自動」「人の確認不要」「必ず受注」などの誤認表現は使用していません。

## 9. PDFについて

`ProposalPilot_LP_v1.pdf` は、`ProposalPilot_LP_Copy.md` と `ProposalPilot_LP_v1.html` の構成に合わせて作成したA4縦8ページの確認用PDFです。正式公開前には、ブラウザでHTMLの表示を確認し、必要に応じて実スクリーンショットやリンク先URLを差し替えてください。
