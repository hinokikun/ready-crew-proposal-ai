# Story Engine Specification

## Purpose

Story Engineは営業提案専用の構成生成エンジンであり、固定スライド順ではなく、顧客、課題、意思決定者、提案条件に応じてStory TypeとSlide Planを決める。

## Inputs

- ProposalBrief
- Customer profile
- Industry
- Decision maker
- Problems and risks
- Goal and scope
- Budget and deadline
- Competitors
- Evidence
- Past proposal references

## Outputs

- Story Type
- Selection Reason
- Primary Audience
- Main Thesis
- Story Flow
- Slide Plan
- Missing Evidence
- Assumptions
- Objections
- Answers
- Next Action
- Confidence

## Story Types

| Type | Use Case |
|---|---|
| 課題解決型 | 顕在課題が明確 |
| 経営課題型 | 役員、投資判断、ROI |
| 成長戦略型 | 売上、事業拡大 |
| 競合差別化型 | 比較検討が強い |
| DX推進型 | 業務変革、全社施策 |
| AI導入型 | AI-OCR、画像認識、生成AI |
| 新規事業型 | 仮説検証、PoC |
| コスト削減型 | 工数、費用削減 |
| Web改善型 | サイト、集客、CV |
| EC改善型 | 購買、CRM、LTV |
| 採用強化型 | 採用サイト、応募導線 |
| ブランド刷新型 | 認知、信頼、表現 |
| 複合型 | 複数目的 |

## Slide Plan Fields

- Slide ID
- Slide Type
- Objective
- Audience Insight
- Core Message
- Evidence
- Visual Intent
- Expected Reaction
- Next Transition
- Risk
- Confidence

## Non Fabrication Rule

根拠がない情報は、以下のいずれかとして扱う。

- `missing`: 不足
- `hypothesis`: 仮説
- `assumption`: AI推定
- `needs_confirmation`: 要確認

断定表現、実績値、ROI、受注確率、顧客固有情報を根拠なしに生成してはならない。

## Human Review

Confidenceが低い、Evidence不足、見積とStoryが不整合、意思決定者が不明な場合はHuman Review必須。

