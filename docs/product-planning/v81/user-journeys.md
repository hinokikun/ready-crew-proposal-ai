# User Journeys

## Journey A: 案件概要から最短でPowerPointを作る

- 開始条件: member以上でログイン済み。
- 操作手順: ホーム -> 新規提案 -> クイック入力 -> AI生成 -> 提出前チェック -> PowerPoint生成。
- 画面遷移: SCR-010 -> SCR-020 -> SCR-130 -> SCR-150。
- AI処理: Proposal生成、カテゴリ判定、見積候補。
- 保存処理: 現在は履歴と一部localStorage。将来はGenerationJobとProposalVersion。
- エラー処理: 入力不足、認証切れ、生成失敗、PPTX失敗。
- 完了条件: PPTXファイルを取得。
- 代替フロー: PDFまたはBeautiful.aiへ出力。
- 権限制御: viewer不可。

## Journey B: AIの質問へ回答しながら高品質な提案書を作る

- 開始条件: 新規提案画面を開く。
- 操作手順: Prompt Builder -> AI確認質問 -> 不足情報補足 -> Story確認 -> Studio。
- AI処理: 不足情報判定、質問優先度、Story Type選択。
- 保存処理: Version82以降でProposalBriefに保存。
- 完了条件: Slide Outlineが承認される。
- 代替フロー: クイック入力へ戻る。
- 権限制御: member以上。

## Journey C: 既存Proposalを開いて編集する

- 現在状態: 作成履歴閲覧は実装済み。Proposal Studioで既存Proposalを完全編集する機能は未実装。
- 将来フロー: 提案履歴 -> Proposalを開く -> 読み取り専用/互換変換 -> Studio編集。
- 保存処理: ProposalVersionを追加。
- エラー処理: 旧形式変換不可時は読み取り専用表示。

## Journey D: Storyを修正してPPTへ反映する

- 現在状態: V80 UIでStory/Slide Outlineは編集可能に見えるが、永続化とPPTX全反映は限定的。
- 将来フロー: Story確認 -> Slide Plan編集 -> Human Review -> Designer -> PPTX。
- 権限制御: member編集、manager承認オプション。

## Journey E: 生成されたPPTをAIで改善する

- 現在状態: Presentation Review / Proposal Optimizationは実装済み。V80右ペインAI編集はUI中心。
- 将来フロー: Studio -> Quality -> 改善案 -> Preview -> 適用 -> Version保存。
- エラー処理: AI失敗時は元スライド保持。

## Journey F: テンプレートやブランドを選択する

- 現在状態: 8テンプレート選択とPPTX request fieldは実装済み。Brand Kit永続化は未実装。
- 将来フロー: テンプレート -> Brand Kit -> Preview -> PPTX。
- 権限制御: memberは選択可、adminはWorkspace既定を管理。

## Journey G: Beautiful.aiへ出力する

- 現在状態: Quality Gate、status、diagnostics、Prompt API、URL解決が実装済み。
- 操作手順: Proposal完成 -> 提出前チェック -> Beautiful.ai作成 -> editorUrl/playerUrlを開く。
- エラー処理: 未設定、認証切れ、権限不足、API失敗、URLなし、ポップアップブロック。

## Journey H: PDFと見積を出力する

- 現在状態: 見積PDF出力あり。
- 将来: Estimate PackをProposal Studioと連動し、本文との整合性をQuality Scoreへ反映。

## Journey I: 提案履歴を確認する

- 現在状態: CreationHistoryPanelとCSV出力あり。
- 将来: ProposalVersion、ExportArtifact、QualityReportを紐づけて再開可能にする。

## Journey J: 業務改善効果を記録する

- 現在状態: 業務改善レポート、CSV、ダッシュボード、研修提出文面生成あり。
- 将来: Proposal単位の時間計測と自動集計を強化。

## Journey K: 管理者がユーザー、ログ、統計を確認する

- 現在状態: Admin panels、Audit Log、Diagnostics、User Managementあり。
- 将来: system administrator分離、Feature Flag管理、Object Level監査を追加。

