# ProposalPilot Category Estimate Packs

Status: design specification only.

## 1. Universal Estimate Rules

- Do not generate a formal quote without source data.
- Do not treat a budget cap as a proposed price.
- Show cost categories as scope blocks.
- Show conditions required for final quote.
- Close with next actions that help the customer decide.

## 2. Category Estimate Items

| Pack | Cost / scope categories |
|---|---|
| Vision / OCR | 要件・評価設計, データ準備, AI検証, 確認UI, システム連携, 運用 |
| Automation | 業務分析, 自動化設計, シナリオ実装, 例外処理, 運用監視 |
| Conversational AI | 会話設計, ナレッジ整備, AI構築, チャネル連携, 運用改善 |
| Knowledge AI | 文書調査, データ整備, 検索基盤, UI, 権限・運用 |
| CRM | 業務要件, データ設計, CRM設定, 外部連携, 定着支援 |
| Generative AI | ユースケース設計, ガイドライン, PoC, 利用環境, 教育, ガバナンス |
| Digital Experience | 調査・戦略, UX / IA, デザイン, 開発, CMS, コンテンツ, 運用・計測 |
| Generic | 調査, 設計, 実行支援, 定着, 改善 |

## 3. Budget Cap Handling

If a budget cap exists, display it as:

- Budget upper limit
- Scope planning constraint
- Final quote pending conditions

Do not display it as:

- Proposed price
- Accepted quote
- Guaranteed delivery amount

## 4. Next Action Pattern

Each estimate slide should include 3-5 next actions:

- Confirm sample data or current process.
- Confirm target scope.
- Confirm evaluation criteria.
- Confirm integration conditions.
- Agree next meeting or decision gate.

## 5. Production Risk

Estimate packs are high-risk because wrong cost categories can make a proposal look fake. Version40 should bind estimate items to category and require project-specific scope validation.
