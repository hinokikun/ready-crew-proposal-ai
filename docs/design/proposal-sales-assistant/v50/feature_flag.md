# Feature Flag

## Backend

Environment variable:

```text
SALES_ASSISTANT_ENABLED=false
```

Default is false.

When false:

- `GET /api/sales-assistant/status` returns enabled false.
- `POST /api/sales-assistant/generate` is rejected.
- No generator execution occurs.

## Frontend

Environment variable:

```text
NEXT_PUBLIC_SALES_ASSISTANT_ENABLED=false
```

Default is false.

When false:

- The admin UI entry is hidden.

## Security Note

The frontend flag is only a display control. Backend role checks and backend feature flag checks are mandatory and authoritative.

## Suggested Enablement Order

1. Enable backend flag in a non-production environment.
2. Enable frontend flag.
3. Confirm admin-only visibility.
4. Confirm member/viewer cannot call the API.
5. Confirm no DB persistence.
6. Run UAT.
