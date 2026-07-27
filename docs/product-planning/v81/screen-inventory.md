# Screen Inventory

| Screen ID | 画面名 | URL案 | 目的 | Role | 主要コンポーネント | 参照API | 保存API | 状態 | 実装状況 |
|---|---|---|---|---|---|---|---|---|---|
| SCR-001 | Login | `/login` | 認証 | all | AuthGate | `/api/auth/status` | `/api/auth/login` | loading/error | 実装済み |
| SCR-010 | Home | `/home` | 今日の提案状況 | all | ProposalAgentDashboard, GuidedFlow | dashboard/logs | none | empty/error | 部分実装 |
| SCR-020 | Proposal Create | `/proposals/new` | 新規開始 | member+ | Prompt Builder | none | 将来Brief | draft/error | UIのみ |
| SCR-030 | Prompt Builder | `/proposals/new/prompt` | 案件情報入力 | member+ | ProposalExperienceStudio | none | 将来Brief | validation | UIのみ |
| SCR-040 | AI Questions | `/proposals/new/questions` | 不足補足 | member+ | Smart Prompts | none | 将来Brief | empty | UIのみ |
| SCR-050 | Strategy Review | `/proposals/new/strategy` | 戦略確認 | member+ | Strategy summary | Strategy CLI/API将来 | Review result | rejected | 設計/部分 |
| SCR-060 | Story Review | `/proposals/new/story` | Story確認 | member+ | Story Engine panel | none | StoryPlan将来 | loading | UIのみ |
| SCR-070 | Slide Outline | `/proposals/new/outline` | 構成編集 | member+ | Slide Outline | none | SlidePlan将来 | conflict | UIのみ |
| SCR-080 | Proposal Studio | `/proposals/:id/studio` | 編集中心 | member+ | 3 panes | Proposal data将来 | Version保存 | autosave | UIのみ |
| SCR-090 | Presentation Designer | `/proposals/:id/design` | 見せ方選択 | member+ | Template picker | none | Template setting将来 | preview | 部分実装 |
| SCR-100 | Quality Check | `/proposals/:id/quality` | 品質評価 | member+ | Quality score | Quality API将来 | Quality report | warning | UIのみ |
| SCR-110 | Generation Progress | `/jobs/:id` | 進捗確認 | member+ | Timeline | Job API将来 | none | retry | 未実装 |
| SCR-120 | Generation Complete | `/proposals/:id/complete` | 出力完了 | member+ | Export links | artifacts将来 | logs | partial | 部分実装 |
| SCR-130 | Proposal History | `/history` | 履歴確認 | member+ | CreationHistoryPanel | `/api/logs/creation-history` | none | empty | 実装済み |
| SCR-140 | Project List | `/projects` | 案件一覧 | member+ | CrmPanel | `/api/projects` | `/api/projects` | empty | 実装済み |
| SCR-150 | AI Sales Secretary | `/assistant` | 相談/改善 | member+ | Copilot, SalesAssistant | sales/proposal-agent | memory/generate | disabled | 部分実装 |
| SCR-160 | Business Improvement | `/improvement` | 効果測定 | member+ | BusinessImprovementReportPanel | logs | report/demo | empty | 実装済み |
| SCR-170 | Analytics | `/analytics` | KPI | manager+ | Dashboards | analytics/logs | none | empty | 実装済み |
| SCR-180 | Admin | `/admin` | 管理 | admin | Admin panels | users/admin/system | users/settings | forbidden | 実装済み |
| SCR-190 | Settings | `/settings` | Workspace/診断 | manager+ | WorkspaceSwitcher, Diagnostics | org/system | context | error | 部分実装 |
| SCR-200 | Template Library | `/templates` | PPTテンプレート | member+ | Designer | none | future | preview | 部分実装 |
| SCR-210 | Brand Settings | `/templates/brand` | Brand Kit | admin/manager | Brand form | future | future | validation | 未実装 |

## Standard States

- Loading: skeletonまたは進捗ラベル。
- Empty: 次に行う主操作を1つ提示。
- Error: 何が起きたか、次に何をするか、request_idがあれば表示。
- Permission: 403時は権限確認を案内し、機能を非表示または読み取り専用化。
- Responsive: 900px未満はサイドバードロワー、Studioはタブ化。

