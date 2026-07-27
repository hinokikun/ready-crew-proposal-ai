# Version81 Summary

Ready Crew Proposal AI / ProposalPilot

作成日: 2026-07-26

---

## プロジェクト名

Ready Crew Proposal AI / ProposalPilot
AI営業秘書

## 目的

営業担当者が案件情報から提案戦略、提案ストーリー、PowerPoint構成、資料品質確認までを一貫して行えるようにすること。

## 背景

従来の提案書作成では、案件入力後にAIが提案書を生成し、人間が結果を確認する流れが中心でした。しかし実務では、提案戦略、意思決定者への訴求、スライド構成、資料品質確認が分断されやすく、営業担当者ごとの品質差も出やすい状態でした。

## 解決した課題

- 提案前に「誰に、何を、どの順番で伝えるか」を整理しにくい。
- AIが生成した提案を人間が確認、編集、採用する場所が不足していた。
- スライドごとの最適なLayout判断が属人的だった。
- 資料品質をスコア、理由、改善案として確認しにくかった。
- 画面上のLayout / Quality判断とPPTX生成のつながりが弱かった。

## 実装した主な機能

- Presentation Quality Engine
- PPT Quality Integration
- Presentation Designer AI
- Designer AI to PPTX Integration
- Sales Strategy AI
- Proposal Strategy Workspace

## 使用技術

| 領域 | 技術 |
|---|---|
| Frontend | Next.js / React / TypeScript / Playwright |
| Backend | FastAPI / Python / Pydantic / pytest |
| PPT Engine | python-pptx系の既存サービス層 |
| AI補助 | Strategy Engine / Sales Strategy AI / Presentation Designer AI |
| 品質確認 | Presentation Quality Engine / Quality Rule Engine |

## AIの特徴

Version81では、AIを「提案書を作るだけの機能」ではなく、「営業担当者と一緒に提案戦略と資料品質を完成させる支援役」として位置づけました。

- Sales Strategy AIが意思決定者、競合状況、勝ち筋、想定反論を整理する。
- Proposal Strategy Workspaceで営業担当者がAI案を編集し、差分とStrategy Scoreを確認する。
- Presentation Designer AIがSlide Type、文章量、数値、Audience、ToneをもとにLayoutを提案する。
- Presentation Quality Engineが18カテゴリで資料品質を評価し、改善理由とAuto Fixを提示する。

## 成果

- Version81の6 Phaseを実装・文書化した。
- 研修発表用のCompletion Report、Demo Script、Demo Data、Runbookを整備した。
- デモ用PPTX、要約PPTX、Quality Report、Sales Strategy Brief、Workspaceサンプルを外部APIなしで生成した。
- Version81関連E2E、Backend対象pytest、typecheck、build、compileall、pip checkが成功した。

## 今後の課題

- Proposal Strategy WorkspaceのDB永続保存
- ProposalVersionによる履歴管理
- Generation JobとQueueによる非同期生成
- Knowledge AIによる過去提案、顧客情報、業界知識の活用
- 共同編集、承認履歴、Review Comment
- 本番運用に向けた監査ログと権限確認の強化
