# Security

## Access Control

- Backend requires admin role.
- Frontend hides the panel unless the public display flag is enabled.
- Frontend hiding is not trusted for authorization.

## Data Handling

- Input is not saved to the database.
- Output is not saved to the database.
- No email is sent.
- No external AI API is called.
- No Beautiful.ai request is made.

## Input Controls

- Request size limit is enforced.
- String fields are length-limited.
- List fields are count-limited.
- Control characters are stripped.
- Missing information is shown as Human Review context.

## Logging

Logs must not include:

- Password
- Token
- Authorization header
- API key
- Customer input全文
- Generated brief全文

## Review Controls

Term Guard output is shown in the result. If a conflicting term is removed or replaced, Human Review remains required.
