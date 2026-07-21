# Version 51 Frontend UI

The admin Sales Assistant panel now shows a Proposal Preview card after Sales Assistant Brief generation.

## UI Behavior

- The `提案書を生成` button appears only after Sales Assistant generation.
- If `SALES_ASSISTANT_PROPOSAL_ENABLED` is false, the button is disabled and the reason is shown.
- If Proposal Preview generation fails, the Sales Assistant Brief remains visible.
- The admin can retry only the Proposal Preview step.
- JSON is hidden by default and can be opened for verification.

## Copy Buttons

- `Proposal概要コピー`
- `スライド構成コピー`
- `全文コピー`

## Human Review

If Strategy Brief or Sales Assistant Brief requires review, the Preview card also shows the review warning and reasons.
