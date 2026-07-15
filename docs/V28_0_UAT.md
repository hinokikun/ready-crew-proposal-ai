# Version 28.0 UAT

## 確認対象

1. 一般利用者ログイン
2. Home表示
3. 新しい提案を作成
4. STEP 1 案件入力
5. STEP 2 AI分析
6. STEP 3 内容確認
7. STEP 4 提出前チェック
8. 未確認項目数の表示
9. 全チェック後の完了ボタン有効化
10. STEP 5 出力
11. 要約PowerPoint
12. 詳細PowerPoint
13. 見積PDF
14. Beautiful.ai disabled理由
15. Beautiful.ai作成成功時のリンク表示
16. STEP 6 AIレビュー・改善
17. STEP 7 完了
18. 管理者ログイン
19. 管理コンソール表示
20. 360px / 390px / 768px / 1024px / 1440px表示

## 合格条件

- 一般利用者が技術診断を見なくても操作できる
- 主ボタンが各ステップで明確
- 提出前チェック完了方法が分かる
- Beautiful.aiが押せない理由が日本語で分かる
- 管理者機能が一般フローに混ざらない

## 重大不具合

以下が発生した場合は本番反映を止める。

- ログイン不可
- 案件入力不可
- AI生成不可
- 提出前チェック完了不可
- PPTX / PDF / Beautiful.ai出力不可
- 権限漏れ
- Organization / Workspace越境
