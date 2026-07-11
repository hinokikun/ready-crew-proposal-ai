# Dependency Audit

Last updated: 2026-07-11

## Scope

- Frontend: `npm.cmd audit --omit=dev`
- Backend: `.\.venv\Scripts\python.exe -m pip check`
- Backend inventory: `.\.venv\Scripts\python.exe -m pip list --format=freeze`

## Frontend Result

`npm.cmd audit --omit=dev` currently exits with findings.

| Package | Severity | Advisory | Status |
| --- | --- | --- | --- |
| `playwright` / `@playwright/test` | High | GHSA-7mvr-c777-76hp | No fix available in current audit output |
| `postcss` via `next` | Moderate | GHSA-qx2v-qp2m-jg93 | No fix available in current audit output |

Notes:

- The Playwright finding affects the test runner/browser download path, not runtime application code served to users.
- The PostCSS finding is reported through the current Next.js dependency chain.
- Keep these advisories on the RC1 watch list and re-run audit after dependency releases.

## Backend Result

`pip check` result:

```text
No broken requirements found.
```

## Backend Package Inventory

```text
alembic==1.18.5
anyio==4.14.1
certifi==2026.6.17
charset-normalizer==3.4.9
click==8.4.2
colorama==0.4.6
distro==1.9.0
fastapi==0.115.12
greenlet==3.5.3
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.18
iniconfig==2.3.0
jiter==0.16.0
lxml==6.1.1
Mako==1.3.12
MarkupSafe==3.0.3
openai==1.109.1
packaging==26.2
pillow==12.3.0
pip==25.0.1
pluggy==1.6.0
psycopg==3.3.4
psycopg-binary==3.3.4
pydantic==1.10.24
Pygments==2.20.0
pytest==8.4.2
python-dotenv==1.2.2
python-pptx==1.0.2
reportlab==4.5.1
sniffio==1.3.1
SQLAlchemy==2.0.51
starlette==0.46.2
tqdm==4.68.4
typing_extensions==4.16.0
tzdata==2026.3
uvicorn==0.34.0
xlsxwriter==3.2.9
```

## RC1 Decision

- Backend dependency health: pass.
- Frontend dependency audit: conditional pass with known advisories and no automated fix available.
- Re-run both checks before v1.0 release and after any Next.js or Playwright dependency update.
