# Version 81 AI Sales Secretary Product Planning Pack

このPlanning Packは、AI営業秘書 / Ready Crew Proposal AI のVersion 81以降の開発基準です。Version 80までの実装を調査し、実装済み、部分実装、UIのみ、APIのみ、設計のみ、未実装を分けて記録します。

## 読む順番

1. `current-state-audit.md`
2. `product-vision.md`
3. `business-problems.md`
4. `information-architecture.md` と `navigation-map.md`
5. `screen-inventory.md`
6. `proposal-studio-spec.md`
7. `prompt-builder-spec.md`
8. `story-engine-spec.md`
9. `presentation-ai-engine/overview.md`
10. `ai-data-contracts.md`
11. `data-model.md` と `api-design.md`
12. `ppt/ppt-design-principles.md`
13. `presentation-quality-score.md`
14. `test-strategy.md`
15. `version-81-90-roadmap.md`
16. `prioritization.md`
17. `decision-log.md`
18. `glossary.md`

## 現在実装と将来構想の区別

- **実装済み**: 現在のコードまたはテストで確認できるもの。
- **部分実装**: UI、API、テスト、設計の一部は存在するが、保存、統合、運用品質が未完了のもの。
- **UIのみ**: Frontend上で操作または表示できるが、Backend永続化や実処理に未接続のもの。
- **APIのみ**: Backend APIやCLIは存在するが、Frontend導線が限定的なもの。
- **設計のみ**: docsまたはオフライン設計だけのもの。
- **未実装**: 仕様として必要だが、コード・API・DB・画面が未作成のもの。

## 主要ドキュメント

| 領域 | 文書 |
|---|---|
| 現状監査 | `current-state-audit.md` |
| プロダクト定義 | `product-vision.md`, `business-problems.md` |
| 権限 | `roles-and-permissions.md` |
| 画面 | `information-architecture.md`, `screen-inventory.md`, `screens/` |
| 中核体験 | `proposal-studio-spec.md`, `prompt-builder-spec.md`, `story-engine-spec.md` |
| AI | `presentation-ai-engine/`, `ai-data-contracts.md` |
| DB/API | `data-model.md`, `migration-roadmap.md`, `api-inventory.md`, `api-design.md` |
| PPT | `ppt/`, `presentation-quality-score.md` |
| 運用品質 | `non-functional-requirements.md`, `security-design.md`, `observability-design.md`, `test-strategy.md` |
| 計画 | `version-81-90-roadmap.md`, `dependency-map.md`, `prioritization.md` |

## Version 81〜90ロードマップ概要

1. Version 81: Presentation AI Engine Foundation
2. Version 82: Proposal Studio
3. Version 83: Stable Save and Generation Jobs
4. Version 84: Knowledge AI
5. Version 85: Proposal OS Core
6. Version 86: Collaboration and Review
7. Version 87: Enterprise Governance
8. Version 88: Automation and Integrations
9. Version 89: Performance and Scale
10. Version 90: External Product Release Candidate

## 設計変更時の更新方法

設計変更を行う場合は、必ず該当文書、`decision-log.md`、`dependency-map.md`、`version-81-90-roadmap.md`を同時に確認します。実装済みの記載を増やす場合は、対応するコード、API、DB、テスト、または画面を明記してください。

## Codex実装時の参照方法

CodexへVersion 81以降の実装を依頼する場合は、最初にこのREADMEと対象領域の仕様書を参照させてください。新機能実装時は、`current-state-audit.md`の現状分類を更新し、既存のFeature Flag、権限、Workspace / Organization境界を維持してください。

