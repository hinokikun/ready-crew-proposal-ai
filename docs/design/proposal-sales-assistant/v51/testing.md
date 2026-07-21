# Version 51 Testing

## Backend

Added coverage:

- Proposal Preview success
- Feature Flag off
- admin-only access
- member rejection
- safe error response
- Human Review propagation
- Version 41 Strategy Brief compatibility
- Version 49 Sales Assistant Brief compatibility
- no DB persistence from Proposal Preview

## Frontend

Added coverage:

- Proposal Preview card display
- copy buttons
- JSON toggle
- Feature Flag disabled reason
- retry path after Proposal Preview error
- Sales Assistant result remains visible after Proposal Preview failure

## Required Checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check

cd ..\frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```
