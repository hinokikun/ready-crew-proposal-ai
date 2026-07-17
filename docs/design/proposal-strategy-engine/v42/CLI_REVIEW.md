# CLI Review

Status: implemented as offline command only.

## Markdown Review Command

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --review ai_ocr
```

## JSON Strategy Brief Command

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --fixture ai_ocr
```

## Output

`--review` prints a Markdown document with:

- Summary
- Main Message
- Review Targets
- Priority Messages
- Risk Messages
- Next Actions
- Evidence
- Human Review Reasons
- Selection Reasons
- Override Rules
- Review Result checklist

## Boundary

This command does not:

- call API
- write DB
- generate PPTX
- call Presentation Engine
- call external services
