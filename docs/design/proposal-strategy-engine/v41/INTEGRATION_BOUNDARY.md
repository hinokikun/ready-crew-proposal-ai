# Integration Boundary

Status: strict boundary for Version 41.

## Not Connected

Version 41 is not connected to:

- FastAPI routers
- `main.py`
- proposal generation services
- PPTX generation services
- frontend UI
- database models
- migrations
- OpenAI calls
- external services
- deployment settings

## Allowed Usage

Allowed usage is limited to:

- backend unit tests
- offline CLI command
- design validation
- Golden JSON comparison

## Future Version 42 Integration Candidates

If humans approve the evaluator, future integration may connect:

- project intake -> Strategy Brief
- Strategy Brief -> Presentation Pack selection
- Strategy Brief -> PPTX generation input
- Strategy Brief -> human review UI
- Strategy Brief -> audit log

Those integrations are explicitly outside Version 41.
