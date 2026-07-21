# Testing

## Backend

Required tests:

- Feature Flag false
- Admin-only access
- Member rejection
- Request size limit
- String/list validation
- Deterministic generation
- Contract shape
- Human Review when information is missing
- Term Guard result
- Safe internal error response
- No DB persistence
- No external API client import

## Frontend

Required tests:

- Admin panel visibility
- Member hidden state
- Feature Flag disabled state
- Form validation
- Sample data
- Loading and duplicate-submit prevention
- Result sections
- Copy action
- JSON toggle
- Broken response handling

## Manual UAT

1. Set both feature flags to true in a test environment.
2. Login as admin.
3. Open detailed mode and admin console.
4. Generate a brief with sample data.
5. Confirm Human Review warning.
6. Confirm copy actions.
7. Login as member and confirm the panel is not visible.
8. Disable backend flag and confirm generation is blocked.
