# ProposalPilot LP v1 - Design Handoff

## 1. Overview

| 項目 | 内容 |
|---|---|
| Brand | ProposalPilot |
| Product | AI営業秘書 |
| Tagline | Accelerate Every Proposal. |
| Page type | BtoB SaaS product landing page |
| Output | HTML / PDF / copy / asset list |
| Design direction | Blue, White, Navy, high-trust BtoB SaaS |

## 2. Design Principles

- 余白を広く取り、1セクション1メッセージにする。
- Heroは製品UIモックを背景化し、テキストとCTAを前面に置く。
- 実顧客情報、実メール、実電話、APIキー、request_idは表示しない。
- 未検証の効果数値や受注率向上を使わない。
- ProposalPilotは「AIが全部やる」ではなく「AIが準備を支援し、人が確認する」と表現する。

## 3. Frame Structure

### Frame 1: Navigation

- Sticky top navigation
- Left: ProposalPilot text logo
- Right: 課題 / 機能 / 利用フロー / FAQ / 無料デモを見る

### Frame 2: Hero

- Background: Deep Navy with subtle grid and product UI mock
- Eyebrow: AI営業秘書 / Accelerate Every Proposal.
- H1: 営業提案をAIでもっと速く、もっと美しく。
- Lead: Product overview copy
- CTA: 無料デモを見る / 製品資料ダウンロード
- Visual: 7-step product UI and floating Quality Gate / Beautiful.ai cards

### Frame 3: Problem & Solution

- Two-column comparison
- Left: 営業提案で発生する課題
- Right: ProposalPilotでどう解決するか

### Frame 4: Features

- 8-card feature grid
- Cards: 案件分析, AI生成, 提出前チェック, PowerPoint, Beautiful.ai, PDF, AIレビュー, 管理・履歴

### Frame 5: Workflow

- 7-step flow
- Steps: 案件情報入力, AI作成, 内容確認, 提出前チェック, 出力, AIレビュー, 完了

### Frame 6: Screenshots

- 6 cards using safe UI mock placeholders
- Home, Case input, AI proposal, Quality Gate, Outputs, Admin

### Frame 7: Benefits

- 4 cards
- 営業品質, 教育, 標準化, ナレッジ

### Frame 8: FAQ

- Two-column FAQ with accordion-like rows
- No JavaScript dependency required

### Frame 9: CTA

- Deep Navy band
- CTA title and buttons

### Frame 10: Footer

- ProposalPilot logo
- Product tagline
- Footer navigation
- 未確定項目の注意

## 4. Design Tokens

| Token | Value |
|---|---|
| Proposal Blue | `#155EEF` |
| Deep Navy | `#102A43` |
| Emerald | `#12B76A` |
| Cyan | `#2DE2E6` |
| Background | `#F8FAFC` |
| Surface | `#FFFFFF` |
| Text Primary | `#1D2939` |
| Text Secondary | `#667085` |
| Border | `#E4E7EC` |
| Radius large | `24px` |
| Radius medium | `18px` |
| Max width | `1180px` |

## 5. Typography

| Use | Style |
|---|---|
| Hero H1 | 48-86px, bold, tight leading |
| Section H2 | 34-54px, bold |
| Lead | 18-22px |
| Body | 15-18px |
| Card title | 16-24px, bold |
| Kicker | 13px, uppercase, letter-spaced |

Recommended fonts:

- Japanese: Noto Sans JP
- English: Inter
- Fallback: Segoe UI, system-ui, sans-serif

## 6. Component Notes

### Buttons

- Primary: Blue background, white text, minimum height 48px.
- Secondary: White or translucent background, border, navy or white text.

### Cards

- White surface, subtle border, soft shadow.
- Radius 18-24px.
- Avoid dense text. Use short paragraphs.

### UI Mock

- Safe fictitious UI only.
- No real user names, real company names, API keys, production URLs, request IDs.
- Replace with production screenshots only after masking review.

## 7. Responsive Rules

- Desktop: 1180px centered content, multi-column grids.
- Tablet: 2-column feature and benefit cards.
- Mobile: single-column layout, hidden top nav links, CTA remains visible.
- Avoid horizontal scroll.

## 8. Accessibility Notes

- HTML includes semantic sections, nav, main, footer.
- CTA links have visible text.
- FAQ uses native `details` / `summary`.
- Color states are supported with text labels, not color alone.
- Contrast is high on Navy and Blue sections.

## 9. Open Items

- Official logo
- Product site URL
- Contact form URL
- Download URL
- Terms URL
- Privacy URL
- Pricing copy
- Real product screenshots
- Public demo video

## 10. Handoff Notes

- This is a static promotional LP artifact under `docs/design`.
- It does not modify the application frontend, backend, API, DB, or migration.
- Use `ProposalPilot_LP_v1.html` as the browser preview source.
- Use `ProposalPilot_LP_v1.pdf` as the review PDF.
