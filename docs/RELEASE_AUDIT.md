# Version 14.1 Production Release Audit

## 機能棚卸し

- AI Workspace: AI社員の作業状態、会話履歴、品質ゲート、レビュー連携
- AI Orchestrator: action queue、自律実行、retry、Queue Monitor
- Daily Briefing: 今日対応すべき案件、優先順位、AI社員コメント
- Notification Center: レビュー待ち、期限超過、品質ゲート未完了などのAI通知
- CRM: 顧客、案件、案件詳細、生成履歴
- Project Lifecycle: 受付から完了までのステータス、受注/失注、制作引継ぎ、振り返り
- Review: 上司レビュー依頼、承認、修正依頼、再レビュー
- Quality Gate: 提出前チェック、DLロック、adminバイパス
- Knowledge: 類似案件、成功/失注ナレッジ、承認フロー、品質スコア
- Analytics: Funnel、Feature Usage、Error Ranking、Product改善候補
- Learning: Prompt/Workflow改善候補、Simulation、Release候補
- Prompt Studio: Prompt Version、A/Bテスト、Winner判定、Rollback
- Release Management: リリース記録、社内展開チェック、公開承認
- Integration: 外部連携設定、外部入力、案件化候補、Dry Run、Connector Readiness
- Feedback: 社内試験導入フィードバック、集計
- Admin panels: ユーザー管理、監査ログ、利用状況、運用準備、改善提案

## 表示整理

一般ユーザーの初期表示は次に寄せます。

- 今日のAIブリーフィング
- AI通知
- 案件メール貼り付け
- AI Workspace
- 要約PPTダウンロード

外部連携候補、CRM、会社調査、社内業務AI、管理系パネルは初期表示から外し、詳細メニューまたは管理者メニューへ寄せます。

## 重複・移動方針

- CRM / Project Lifecycle / Review / Quality Gate は案件管理として扱う
- Analytics / Learning / Prompt Studio / 改善提案は改善分析として扱う
- Integration / Dry Run / Connector Readiness は外部連携として扱う
- Knowledge / Template / 承認待ちはナレッジ管理として扱う
- User / Audit / Release / Operation Readiness は運用管理として扱う

## Import監査

- `prompts.py` と `prompts/` の衝突を解消し、旧提案生成Promptは `proposal_prompts.py` に分離
- `app.prompts` はPrompt Registryパッケージとして維持
- `schemas/` はパッケージとして維持
- Vercel向けに存在しないimportがないか `typecheck` / `build` で確認

## 権限監査

- viewer: 生成、編集、承認不可。閲覧中心
- member: 提案作成、PPT/PDF、レビュー依頼、品質ゲート完了
- manager: レビュー承認、リリース承認、一部管理分析
- admin: 全機能、ユーザー管理、監査、バイパス、Prompt Studio

Backend API側でも `require_roles` による権限制御を確認対象にしています。

## セキュリティ監査

- APIキー、token、password、DATABASE_URL全文は画面表示しない
- 外部連携でOAuth token、API key、メール本文全文、添付ファイル本体を保存しない
- Analytics、Knowledge、Audit Logへ案件本文全文や生成本文全文を保存しない
- Prompt StudioはPrompt本文のみ保存対象。顧客情報やAPIキーは保存禁止

## リリース前確認

本監査では以下を実行対象とします。

- `npm.cmd run build`
- `npm.cmd run typecheck`
- `npm.cmd run check:unused`
- `python -m compileall backend/app backend/tests`
- `pytest`
- GitHub Actions設定確認
- Vercel build確認
- Render `/health` 確認
