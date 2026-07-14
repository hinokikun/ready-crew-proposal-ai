# Version 23.2 Test Matrix

目的: commit単位ごとに必要な検証を整理します。

## Frontend-only変更

対象例:

- `frontend/components`
- `frontend/app/styles`
- `frontend/lib`
- `frontend/client-api`
- `frontend/types`
- `frontend/e2e`

実行:

```bat
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

## Backend-only変更

対象例:

- `backend/app`
- `backend/tests`

実行:

```bat
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```

## Migration変更

対象例:

- `backend/alembic/versions/*.py`
- `backend/migrations/README.md`

確認:

- 空DBで初期化できること
- 既存DBで起動時patchが壊れないこと
- PostgreSQL移行方針と矛盾しないこと
- downgrade方針を明確にすること

実行候補:

```bat
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
```

## Docs-only変更

対象例:

- `docs/*.md`
- `README.md`

実行:

```bat
git diff --check
```

任意:

```bat
cd frontend
npm.cmd run build
```

## Commit別 Matrix

| Commit | 主な内容 | 必須テスト | 任意/追加確認 |
|---|---|---|---|
| 1 | Organization / Workspace | Backend compileall, pytest, Frontend build | Workspace越境UAT |
| 2 | Presentation Review | pytest, Frontend build, E2E | Beautiful.ai revision |
| 3 | Proposal Optimization | pytest, Frontend build, E2E | TOP5改善表示 |
| 4 | Beautiful.ai | pytest, Frontend build, E2E | Render `/health`, status route |
| 5 | Architecture Refactoring | 全Frontend, 全Backend | PPTX visual snapshot |
| 6 | Simple Guided UI | typecheck, check:unused, build, E2E | 360px表示 |
| 7 | Tests and smoke | 全Frontend, 全Backend | GitHub Actions |
| 8 | Docs and manuals | git diff --check | Markdown目視 |

## 共通確認

```bat
git diff --check
git status --short
```

## Cloud前の最終ローカル確認

```bat
cd frontend
npm.cmd run typecheck
npm.cmd run check:unused
npm.cmd run build
npm.cmd run test:e2e
```

```bat
cd backend
.\.venv\Scripts\python.exe -m compileall app tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
```
