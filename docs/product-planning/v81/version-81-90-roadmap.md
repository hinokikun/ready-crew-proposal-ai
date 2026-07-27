# Version 81-90 Roadmap

| Version | 目的 | 実装範囲 | 非対象 | DB | Risk |
|---|---|---|---|---|---|
| 81 | Presentation AI Engine Foundation | 設計、contracts、品質ルール、準備 | 本番接続 | no | 文書と実装の乖離 |
| 82 | Proposal Studio | Studio URL化、SlidePlan編集、Autosave | 完全PPT editor | yes | AppShell分割影響 |
| 83 | Stable Save and Generation Jobs | ProposalVersion、GenerationJob、進捗 | Knowledge AI | yes | migration |
| 84 | Knowledge AI | ナレッジ登録、検索、引用 | 外部CRM連携 | maybe | 権限/PII |
| 85 | Proposal OS Core | Project/Proposal/History統合 | SaaS課金 | yes | 既存履歴互換 |
| 86 | Collaboration and Review | コメント、承認、ロック | リアルタイム共同編集 | yes | 権限 |
| 87 | Enterprise Governance | object auth, audit, retention | SSO完全対応 | yes | 運用複雑化 |
| 88 | Automation and Integrations | CRM/Slack/Calendar設計接続 | メール自動送信 | maybe | 外部API |
| 89 | Performance and Scale | paging, lazy load, caching | 新機能 | maybe | regression |
| 90 | External Product RC | SaaS候補、UAT、release gate | 大型機能 | no | commercial readiness |

## Version 81 Minimum Phase

1. Docs review.
2. Schema validation prototype offline.
3. PPT quality rules as pure functions.
4. Legacy compatibility tests.

## Rollback

Feature Flagを必ず維持し、Legacy生成へ戻せる単位で実装する。DB migrationがあるVersionはbackup/restore手順を先に用意する。

