# Evaluator

The offline evaluator returns `SalesAssistantEvaluationReport` with a 100-point score and per-item checks.

## Checks

- schema validity
- strategy alignment
- persona alignment
- decision maker alignment
- question quality
- objection coverage
- evidence safety
- term guard compliance
- follow-up consistency
- human review consistency
- determinism
- unsupported claim count

The evaluator is deterministic and does not call OpenAI or external services.

