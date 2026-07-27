# Information Architecture

Version 80 では、すべての機能を1画面へ縦に並べる構成を避け、利用目的ごとにビューを分けます。

| ビュー | 主な目的 | 対象 |
|---|---|---|
| ホーム | 今日の状況と次アクション確認 | 全ユーザー |
| 新規提案 | Prompt Builderと既存Guided Flow | member以上 |
| 提案エディター | Story確認とスライド編集 | member以上 |
| 提案履歴 | 履歴とCSV確認 | 全ユーザー |
| 案件一覧 | CRMと進行状況 | member以上 |
| AI営業秘書 | Proposal Agent / Copilot | 全ユーザー |
| テンプレート | PPTデザイン選択 | member以上 |
| 分析 | KPIと運用状況 | manager以上 |
| 業務改善 | 研修提出向け効果測定 | 全ユーザー |
| 管理 | ユーザー、監査、UAT | admin |
| 設定 | Workspaceと診断 | manager以上 |

通常モードでは、技術診断、内部ログ、管理者向け分析は表示しません。管理者またはmanagerが詳細モードを開いた場合だけ確認できます。

