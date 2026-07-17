# Version 42 Strategy Brief Human Review Workflow

Status: design and offline review utilities only.

Version 42 defines how a sales representative reviews, edits, approves, rejects, or requests re-evaluation of a Strategy Brief before it can be used by Presentation Engine.

## Boundary

Version 42 does not connect to:

- Presentation Engine
- PPTX generation
- API routes
- frontend UI
- database
- migrations
- OpenAI
- Beautiful.ai

## Workflow

```text
案件入力
-> Strategy Engine
-> Strategy Brief
-> Human Review
-> Approve
-> Presentation Engine
```

The last step is not implemented in Version 42. Strategy Brief must not be passed to Presentation Engine before review approval.

## Files

| File | Purpose |
|---|---|
| `HUMAN_REVIEW_WORKFLOW.md` | End-to-end review workflow. |
| `REVIEW_SCREEN_SPEC.md` | Future screen behavior specification. |
| `OVERRIDE_RULES.md` | Changeable and locked fields. |
| `REVIEW_RESULT_SCHEMA.md` | Review result JSON and report schema. |
| `CLI_REVIEW.md` | Offline Markdown review command. |
| `MARKDOWN_REVIEW_TEMPLATE.md` | Human-readable review template. |
| `REVIEW_RESULT_EXAMPLE.json` | Example review result report. |

## Offline Command

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.strategy_engine.cli --review ai_ocr
```
