# Failure Handling

| Failure | User Message | System Action | Retry |
|---|---|---|---|
| Strategy失敗 | 提案戦略を作成できませんでした | 入力保持 | 可 |
| Story失敗 | ストーリー作成に失敗しました | Safe structure | 可 |
| Layout失敗 | 標準レイアウトで続行します | Corporate Clean | 可 |
| PPTX失敗 | PowerPointを生成できませんでした | Proposal保持 | Exportのみ再試行 |
| Beautiful.ai失敗 | Beautiful.aiで作成できませんでした | PPTXへ誘導 | 可 |
| Autosave失敗 | 保存できていません | ローカル保持 | 可 |

秘密情報、入力全文、APIキー、Tokenはログへ出さない。

