# Word Manual Plan

目的: UAT終了後に、Markdown原稿をもとに Word マニュアルを作成するための構成案です。

今回は `.docx` は作成しません。

## 対象ドキュメント

- 一般利用者マニュアル: `docs/USER_MANUAL_TEXT.md`
- 管理者マニュアル: `docs/ADMIN_MANUAL_TEXT.md`
- スクリーンショット一覧: `docs/SCREENSHOT_LIST.md`
- FAQ: `docs/FAQ.md`
- 操作フロー: `docs/OPERATION_FLOW.md`

## 一般利用者マニュアル 想定ページ数

想定: 20〜30ページ

構成:

1. 表紙
2. 改訂履歴
3. 目次
4. AI営業秘書とは
5. ログイン
6. ホーム画面
7. STEP 1 案件入力
8. STEP 2 AI作成
9. STEP 3 内容確認
10. STEP 4 提出前チェック
11. STEP 5 出力
12. PowerPoint / PDF
13. Beautiful.ai
14. STEP 6 AIレビューと改善
15. Revision
16. STEP 7 完了
17. Workspace切替
18. 通知
19. ログアウト
20. エラー時の対応
21. FAQ
22. 問い合わせ方法

## 管理者マニュアル 想定ページ数

想定: 30〜45ページ

構成:

1. 表紙
2. 改訂履歴
3. 目次
4. 管理者ログイン
5. 詳細モード
6. User Management
7. Organization
8. Workspace
9. Analytics
10. Knowledge
11. Prompt Studio
12. Learning
13. Integrations
14. Pilot
15. Audit Log
16. UAT
17. Beautiful.ai 診断
18. Maintenance
19. Render
20. Vercel
21. GitHub Actions
22. Backup
23. Restore
24. 障害時対応

## 注意書きの書式

Word化時は、注意書きを次の形式で統一します。

- 注意: 誤操作やセキュリティに関わる内容
- ヒント: 操作を楽にする補足
- 補足: 詳しい説明

## Wordで使用する表

使用予定:

- ロール別権限表
- UAT確認表
- エラー一覧
- 出力形式一覧
- 管理者確認項目
- バックアップ・リストア手順表

## 目次

Word の自動目次を使います。

見出し:

- 見出し1: 章
- 見出し2: 節
- 見出し3: 詳細項目

## 改訂履歴

表形式:

| Version | 日付 | 変更内容 | 作成者 |
|---|---|---|---|
| 1.0 |  | 初版 |  |

## バージョン表記

表紙とフッターに次を記載します。

```text
AI営業秘書 利用者マニュアル v1.0
```

または

```text
AI営業秘書 管理者マニュアル v1.0
```

## 発行日

UAT終了後、正式に配布する日付を差し込みます。

```text
発行日: YYYY年MM月DD日
```

## 対象URL

本番URL確定後に差し込みます。

```text
対象URL: https://...
```

## 問い合わせ先

社内運用担当が確定後に差し込みます。

```text
問い合わせ先: 社内AI運用担当
連絡方法: 社内チャットまたは管理者指定の窓口
```

## スクリーンショット差し込み方針

UAT終了後、画面が固まってからスクリーンショットを撮影します。

差し込み予定:

- ログイン画面
- ホーム画面
- STEP 1〜STEP 7
- Beautiful.ai
- Presentation Review
- Proposal Optimization
- Revision
- 管理者画面
