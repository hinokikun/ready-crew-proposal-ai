# Frontend UI

## Location

The UI is placed inside the existing admin console:

`AI Sales Assistant / AI営業アシスタント`

It is not visible to member or viewer users.

## Inputs

Required:

- 案件名
- 案件概要

Optional:

- 顧客名
- 商談段階
- 予算情報
- スケジュール情報
- 既知の要件
- 制約条件
- 過去のやり取り
- 根拠・確認済み情報

## Output Sections

1. Summary
2. Meeting Plan
3. Discovery Questions
4. Talk Track
5. Objection Handling
6. Decision Maker Support
7. Evidence Guidance
8. Next Actions
9. Follow-up
10. Term Guard / Risk
11. Metadata

## Copy Actions

The UI supports copy buttons for:

- サマリー
- 質問
- トーク
- 反論対応
- 次アクション
- フォロー
- 全文

## JSON View

The JSON view is closed by default and only available inside the admin panel.

## Human Review

If `human_review_required` is true, a warning is shown above the result. The UI does not treat the brief as approved.
