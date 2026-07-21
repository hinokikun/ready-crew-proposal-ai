# Version52 Rollback

Version52 adds readiness documentation and tests, plus the Version51 Proposal Preview bridge behind Feature Flags.

## Fast Disable

Set:

```env
SALES_ASSISTANT_PROPOSAL_ENABLED=false
```

This disables only the Sales Assistant to Proposal Preview bridge.

To hide the whole admin UI:

```env
NEXT_PUBLIC_SALES_ASSISTANT_ENABLED=false
SALES_ASSISTANT_ENABLED=false
```

## Code Rollback

Use `git revert` for the specific commit that introduced the problem, then push normally.

Do not use `reset --hard` or force push for shared branches.

## Verification After Rollback

- login
- admin menu
- existing proposal generation
- existing PPTX
- existing PDF
- `/health`
- `/health/ready`
- Sales Assistant status endpoint
