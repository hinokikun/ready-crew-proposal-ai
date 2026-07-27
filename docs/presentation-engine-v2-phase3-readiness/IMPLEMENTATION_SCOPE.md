# Implementation Scope

## Recommended Future Module

```text
backend/app/presentation_engine_v2/visual_director/
  __init__.py
  director.py
  models.py
  rules.py
  scorers.py
  selectors.py
  normalizers.py
  validators.py
  evaluator.py
  schema.py
  fixtures/
  golden/
  README.md
```

## Relationship to Visual Plan Contract

`visual_plan_contract` owns the output model and validation boundary.

Future `visual_director` should own:

- input adaptation
- deterministic rule application
- scoring
- candidate selection
- fallback handling
- output normalization
- offline evaluation
- fixtures and golden cases

Future `visual_director` must not own:

- contract version mutation
- Blueprint Composer output
- coordinates
- theme generation
- PPTX generation
- API connection
- DB persistence
- Version81 runtime connection

## Relative Estimate

| Work Item | Estimate | Dependency |
|---|---|---|
| Contract Adapter | Small | Existing upstream contracts |
| Rule Engine | Medium | Visual Plan rules |
| Scoring | Medium | Rule Engine |
| Selection | Medium | Scoring |
| Validator integration | Small | Visual Plan validators |
| Evaluator | Medium | Generated Visual Plan |
| Fixtures | Medium | Upstream fixture availability |
| Golden | Medium | Deterministic output |
| Tests | Large | Fixtures and golden |
| Docs | Small | Implementation behavior |
| Alpha Integration addition | Medium | Visual Director output |
| Phase4 Handoff | Medium | Visual Plan quality |

## Scope Guard

The first implementation should produce Visual Plan Contract only. It should not
generate slide blueprints or PowerPoint files.
