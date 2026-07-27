# Test Strategy

## Required Phase3 Test Types

| Test Type | Purpose | Suggested Count |
|---|---|---:|
| Unit Test | Validate small rule/scorer functions. | 20+ |
| Contract Test | Ensure Visual Director returns Visual Plan Contract only. | 8+ |
| Schema Test | Validate schema generation and examples. | 6+ |
| Validator Test | Cover current Visual Plan validators. | 15+ |
| Rule Test | Cover visual pattern to strategy mapping. | 20+ |
| Scoring Test | Verify deterministic ranking. | 12+ |
| Selector Test | Verify tie-breaks and fallback. | 12+ |
| Fallback Test | Unknown, weak, and missing input conditions. | 8+ |
| Deterministic Test | Same input produces same output. | 6+ |
| Unicode Test | Japanese and mixed-language cases. | 6+ |
| Deck-level Consistency Test | Cross-slide rhythm and repetition. | 8+ |
| Cross-slide Diversity Test | Prevent same visual overuse. | 8+ |
| Evidence Compatibility Test | Chart/diagram require correct evidence. | 12+ |
| Audience Fit Test | Executive, technical, operations, general. | 8+ |
| Decision Stage Fit Test | Discovery, evaluation, approval, renewal. | 8+ |
| Phase4 Handoff Test | Ensure composer-facing fields are usable. | 8+ |
| Golden Test | Freeze representative outputs. | 20+ |
| Regression Test | Confirm prior contracts remain stable. | 10+ |

## Test Principle

The first Visual Director implementation should be deterministic and fixture
driven. Tests should confirm explainability before visual sophistication.

## Out of Scope

- PPTX visual rendering tests
- Screenshot tests
- Frontend E2E
- OpenAI tests
- Beautiful.ai tests
- DB tests
