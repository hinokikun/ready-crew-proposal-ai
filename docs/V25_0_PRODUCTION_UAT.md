# Version 25.0 Production UAT

## 目的

正式版公開前に、営業担当・管理者・閲覧者の主要操作が本番 URL で問題なく動作することを確認します。

## 実施前提

- 実顧客情報は使用しません。
- 架空会社名、架空担当者、架空要件のみを使用します。
- API キー、Password、Token、実メール本文を入力しません。

## 主要チェック

1. admin ログイン
2. member 作成
3. member ログイン
4. viewer ログイン
5. 無効ユーザーのログイン拒否
6. 案件情報入力
7. AI 提案書生成
8. 内容確認
9. 提出前チェック完了
10. 要約PPTX 出力
11. 詳細PPTX 出力
12. 見積PDF 出力
13. Beautiful.ai 生成
14. Beautiful.ai 失敗時の日本語エラー確認
15. 作成履歴
16. 監査ログ
17. Organization 切替
18. Workspace 切替
19. Organization / Workspace 越境拒否
20. 360px モバイル表示

## 合格条件

- 重大操作に `×` がないこと。
- Organization / Workspace 越境が拒否されること。
- viewer が生成・編集・承認できないこと。
- Beautiful.ai が失敗しても PPTX / PDF 代替導線が表示されること。
- エラー時に `request_id` を確認できること。

## 重大項目

以下が失敗した場合は本番公開不可です。

- ログイン
- 権限拒否
- Organization / Workspace 分離
- AI 生成
- Quality Gate
- PPTX / PDF 出力
- Beautiful.ai
- 監査ログ
- `/health/ready`

## 結果記録

| No | 項目 | 結果 | コメント |
| --- | --- | --- | --- |
| 1 | admin ログイン |  |  |
| 2 | member 作成 |  |  |
| 3 | member ログイン |  |  |
| 4 | viewer ログイン |  |  |
| 5 | 案件入力 |  |  |
| 6 | AI 生成 |  |  |
| 7 | Quality Gate |  |  |
| 8 | 要約PPTX |  |  |
| 9 | 詳細PPTX |  |  |
| 10 | 見積PDF |  |  |
| 11 | Beautiful.ai |  |  |
| 12 | 作成履歴 |  |  |
| 13 | 監査ログ |  |  |
| 14 | Workspace 分離 |  |  |
| 15 | モバイル |  |  |
