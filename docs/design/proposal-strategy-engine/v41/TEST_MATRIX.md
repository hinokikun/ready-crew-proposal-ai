# Test Matrix

Status: implemented for offline evaluator.

## Fixture Coverage

The test suite covers 20 fixtures:

1. AI image recognition
2. AI-OCR
3. RPA
4. AI chatbot
5. Internal knowledge search
6. CRM
7. Generative AI support
8. Web renewal
9. AI-OCR + RPA
10. CRM + Generative AI
11. Web + AI chatbot
12. Generic consulting
13. Sparse input
14. Budget-only input
15. Quality assurance owner case
16. Executive ROI case
17. Information systems security case
18. Field operations case
19. Same project with different persona
20. Mixed category terms

## Assertions

Tests verify:

- Golden JSON consistency
- schema fields
- Generic fallback
- compound category handling
- persona hint priority
- story changes by persona
- budget upper-limit treatment
- human review gate
- term guard
- deterministic output
- no production entrypoint import
- no external service call token in strategy module

## Golden JSON

Golden JSON is stored in:

```text
backend/tests/strategy_engine/golden/expected_strategy_briefs.json
```

It contains stable expected summary fields and confidence ranges.
