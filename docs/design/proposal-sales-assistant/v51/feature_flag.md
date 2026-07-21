# Version 51 Feature Flag

## Backend

```env
SALES_ASSISTANT_ENABLED=false
SALES_ASSISTANT_PROPOSAL_ENABLED=false
```

`SALES_ASSISTANT_PROPOSAL_ENABLED` defaults to `false`.

## Frontend

The UI is still controlled by the Version 50 flag:

```env
NEXT_PUBLIC_SALES_ASSISTANT_ENABLED=false
```

The Proposal Preview button is rendered only after Sales Assistant generation and is enabled only when backend status reports `proposal_preview_enabled=true`.

## Rollback

Set `SALES_ASSISTANT_PROPOSAL_ENABLED=false` to disable only the Proposal Preview bridge while keeping the Sales Assistant UI available.
