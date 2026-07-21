# Human Review Export Rules

## Export可能

| 条件 | Export |
| --- | --- |
| Human Review不要 | 可 |
| Human Review必須かつ`approved` | 可 |
| Human Review必須かつ`exportable` | 可 |

## Export不可

| 状態 | 理由 |
| --- | --- |
| `unreviewed` | 承認未完了 |
| `reviewed` | 確認済みだが承認ではない |
| `needs_revision` | 修正が必要 |
| `regenerate_recommended` | 再生成推奨 |

Frontendの状態だけでExport可能とは判定しない。Backendでも必ず同じ条件を再検証する。
