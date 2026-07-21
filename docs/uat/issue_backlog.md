# UAT Issue Backlog

UATで見つかった不具合、改善要望、確認事項を管理するBacklogです。秘密情報や実顧客情報は記載しないでください。

| ID | 種類 | 重大度 | 内容 | 再現案件 | Role | Organization / Workspace | 状態 | 担当 | 次対応 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UAT-001 | Bug / Improvement / Question | Critical / Major / Minor / Nice to Have |  |  |  |  | Open / Investigating / Fixed / Deferred |  |  |

## 重大度定義

### Critical

- ログイン不能
- admin権限境界の破れ
- Human Review未承認でExport可能
- PPTXが0 byteまたは開けない
- APIキー、Password、Tokenが画面・ログに出る
- Organization / Workspace分離不備

### Major

- Sales Assistant生成不能
- Proposal Preview生成不能
- Export失敗が高頻度
- Beautiful.ai連携失敗が業務に影響
- UAT継続が困難なUI不具合

### Minor

- 文言が分かりづらい
- 手順が迷いやすい
- 表示位置やレスポンシブの小さな崩れ
- Retryやコピー操作の改善要望

### Nice to Have

- 将来的な履歴保存
- ダッシュボード化
- 操作短縮
- レポート自動化

## 状態定義

- Open: 未着手
- Investigating: 調査中
- Fixed: 修正済み
- Deferred: 次Version以降へ延期
- Won't Fix: 対応しない判断
