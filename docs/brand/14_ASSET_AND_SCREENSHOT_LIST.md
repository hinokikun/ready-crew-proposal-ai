# ProposalPilot Asset and Screenshot List

ブランド名: ProposalPilot
製品名: AI営業秘書
目的: パンフレット、カタログ、LP、営業デモで必要な素材とスクリーンショットを整理する。

## 撮影共通ルール

- 実顧客名、実担当者名、実メールアドレス、実電話番号を使用しない。
- APIキー、Password、Token、Authorization、DATABASE_URL、request_idを画面に表示しない。
- デモ素材は `docs/DEMO_DATA.md` の架空データを使用する。
- ブラウザのブックマーク、個人アカウント名、拡張機能が映らないようにする。
- 画面幅はPC 1440px、タブレット 768px、スマートフォン 390pxを必要に応じて撮影する。

## 素材一覧

| 素材 | 目的 | 推奨サイズ | マスキング | 撮影手順 | ファイル名 |
|---|---|---|---|---|---|
| ロゴ | 表紙、LP、デモ資料 | SVGまたは横1200px | 不要 | ブランド確定後に書き出し | proposalpilot-logo.svg |
| ブランドマーク | アイコン、展示会パネル | SVGまたは512px | 不要 | ブランド確定後に書き出し | proposalpilot-mark.svg |
| アプリトップ | 製品概要 | 1440x900 | ユーザー名、組織名を架空化 | adminまたはmemberでログイン | app-home-dashboard.png |
| 案件入力 | 利用フロー説明 | 1440x900 | 案件本文を架空化 | STEP 1を表示 | step1-intake.png |
| AI作成中 | AI支援説明 | 1440x900 | 顧客名を架空化 | STEP 2作成中を表示 | step2-generating.png |
| 内容確認 | 提案内容確認 | 1440x900 | 会社名、金額を架空化 | STEP 3を表示 | step3-review.png |
| 提出前チェック | Quality Gate説明 | 1440x900 | 確認者名を架空化 | STEP 4を表示 | step4-quality-check.png |
| 出力選択 | 成果物紹介 | 1440x900 | 不要 | STEP 5を表示 | step5-output-options.png |
| 要約PPTX | 成果物例 | 16:9 1920x1080 | 顧客名を架空化 | 生成後の表紙を撮影 | output-summary-pptx.png |
| 詳細PPTX | 成果物例 | 16:9 1920x1080 | 顧客名を架空化 | 生成後の代表スライドを撮影 | output-detail-pptx.png |
| 見積PDF | 成果物例 | A4縦相当 | 金額を架空化 | PDFプレビューを撮影 | output-estimate-pdf.png |
| Beautiful.ai完成画面 | 連携説明 | 1440x900 | URL、顧客名を架空化 | Beautiful.ai生成後画面を撮影 | beautiful-ai-complete.png |
| 作成履歴 | 履歴機能説明 | 1440x900 | 顧客名を架空化 | 履歴一覧を表示 | creation-history.png |
| ユーザー管理 | 管理者機能説明 | 1440x900 | メールを架空化 | 管理者でユーザー一覧を表示 | admin-user-management.png |
| 監査ログ | 監査説明 | 1440x900 | user_id、request_idを非表示 | 監査ログ一覧を表示 | admin-audit-log.png |
| 診断画面 | Beautiful.ai診断 | 1440x900 | APIキー非表示を確認 | 管理者診断を表示 | admin-beautiful-diagnostics.png |

## 個人情報のマスキング

- 実名、実メール、実電話番号、実会社名は使用しない。
- 架空会社名は「株式会社サンプル」「サンプル営業部」などに統一する。
- スクリーンショットにログイン中ユーザーの実名が出る場合は、撮影前に架空ユーザーへ変更する。
- 管理者画面のメールアドレスは `user@example.com` 形式の架空アドレスにする。

## APIキー・診断情報の確認

撮影前に以下が映っていないことを確認する。

- APIキー
- Password
- Token
- Authorization
- DATABASE_URL
- OpenAIキー
- Beautiful.aiキー
- request_id
- Renderログ
- GitHub認証情報

## 推奨スクリーンショット順

1. アプリトップ
2. 案件入力
3. AI作成中
4. 内容確認
5. 提出前チェック
6. 出力選択
7. 要約PPTX
8. 詳細PPTX
9. 見積PDF
10. Beautiful.ai完成画面
11. 作成履歴
12. ユーザー管理
13. 監査ログ
14. 診断画面

## 不足素材

- ProposalPilot正式ロゴ
- ブランドマーク
- 製品サイト用OGP画像
- 展示会パネル用高解像度画像
- 公開可能なサンプル成果物
- デモ動画
- QRコード
