# Information Architecture

## Principle

- 1画面1目的。
- 一般ユーザーと管理者を分離。
- Proposal作成に直結する導線を最短化。
- 低頻度機能は管理、設定、業務改善へ寄せる。
- URL設計は将来導入し、現状のV80はAppShell内ビュー切替。

## Top Level Navigation

| Menu | 目的 | 対象Role | 主要操作 | 子画面 | 関連API | 現在状態 | 将来 |
|---|---|---|---|---|---|---|---|
| ホーム | 今日の提案状況 | all | 新規提案開始、最近案件 | ToDo, Recent | `/api/proposal-agent/dashboard`, logs | 部分実装 | Personalized home |
| 新規提案 | 案件入力 | member+ | Prompt Builder, Quick入力 | AI質問, 確認 | Proposal生成API | UIのみ/既存生成接続 | URL化、保存 |
| 提案スタジオ | Story/Slide編集 | member+ | Slide編集, Quality | AI, Design, Comments | 将来Slides API | UIのみ | Version82中心 |
| 案件 | Project/CRM | member+ | 案件一覧、進行管理 | CRM, lifecycle | `/api/projects` | 実装済み | Proposalと統合 |
| 提案履歴 | 過去提案 | member+ | 再開、再出力、CSV | Export履歴 | `/api/logs/creation-history` | 実装済み | Version保存 |
| AI営業秘書 | Copilot/Agent | member+ | 質問、改善提案 | Chat, ToDo | sales/proposal-agent | 部分実装 | Context-aware |
| テンプレート | PPTデザイン | member+ | Template選択 | Brand Kit | PPTX request | 部分実装 | Workspace既定 |
| ナレッジ | 事例/過去提案 | manager+ | 検索、登録 | RAG, Best Practice | `/api/knowledge` | 部分実装 | Version84 |
| 分析 | KPI | manager+ | Dashboard, CSV | Usage, Quality | analytics/logs | 実装済み | 統合指標 |
| 業務改善 | 時間短縮 | member+ | レポート記録 | Training summary | `/api/logs/business-improvement-reports` | 実装済み | Proposal連動 |
| 管理 | ユーザー/監査 | admin | User, Audit, UAT | Diagnostics | admin/users/system | 実装済み | Governance |
| 設定 | Workspace/環境 | manager+ | Workspace, diagnostics | Feature Flags | organizations/system | 部分実装 | 管理権限分離 |

## Recommended URL Design

現状は単一AppShellでビュー切替。将来は以下へ移行する。

- `/home`
- `/proposals/new`
- `/proposals/:proposalId/studio`
- `/projects`
- `/history`
- `/assistant`
- `/templates`
- `/knowledge`
- `/analytics`
- `/improvement`
- `/admin`
- `/settings`

## Mobile

スマートフォンでは固定サイドバーをドロワー化し、提案作成中は下部に「次へ」「保存」「プレビュー」を固定表示する。管理画面はカードリストへ切り替える。

