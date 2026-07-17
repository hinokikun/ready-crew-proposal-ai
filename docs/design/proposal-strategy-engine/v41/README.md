# Version 41 Proposal Strategy Brief Evaluator

Status: offline implementation and test specification only.

Version 41 turns the Version 40 design into an independent evaluator that can produce a structured `StrategyBrief` from project information.

It is not connected to production API, frontend UI, database, Presentation Engine, PPTX generation, or external services.

## Added Areas

- Strategy Brief schema
- input schema
- enum definitions
- deterministic rule evaluator
- confidence model
- human review gate
- term guard
- fixtures
- Golden JSON tests
- offline CLI execution

## Execution

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --fixture ai_ocr
```

## Boundary

The evaluator is only usable from tests or offline commands. Version 42 or later must receive human approval before production flow integration.
