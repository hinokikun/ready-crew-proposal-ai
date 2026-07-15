# Contributing

Thank you for contributing to AI営業秘書.

This project is currently prepared for controlled production rollout. Contributions should prioritize stability, security, maintainability, and operational clarity.

## Basic rules

- Do not add new sales AI features without an approved requirement.
- Do not change API contracts, DB schema, migrations, or permissions casually.
- Do not commit secrets, API keys, passwords, tokens, customer body text, or generated full text.
- Keep changes small and scoped.
- Preserve existing PPTX, PDF, Beautiful.ai, Quality Gate, Organization, Workspace, and role behavior.

## Development flow

1. Confirm the issue and expected behavior.
2. Create a focused change.
3. Run Backend tests if Backend is affected.
4. Run Frontend typecheck/build/E2E if Frontend is affected.
5. Run `git diff --check`.
6. Review staged diff before commit.
7. Use a clear commit message.

## Required checks

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

Common:

```powershell
git diff --check
```

## Pull request checklist

- [ ] Purpose and scope are clear
- [ ] No secret values are included
- [ ] No unrelated formatting churn
- [ ] Tests are listed with results
- [ ] UI/API/DB compatibility impact is described
- [ ] Rollback notes are included when needed

## Security

If you find a vulnerability, do not open a public issue with exploit details. Follow `SECURITY.md`.
