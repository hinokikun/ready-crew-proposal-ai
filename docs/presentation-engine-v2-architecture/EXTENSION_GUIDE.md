# Extension Guide

## Safe Extension Points

Future teams may add:

- Localization
- Accessibility checks
- Animation hints
- Brand theme mapping
- Corporate design templates
- Industry templates
- Multilingual message variants
- Review engines
- Quality engines
- Semantic validators

## Extension Pattern

1. Define contract.
2. Add deterministic model and schema.
3. Add normalizer.
4. Add validator.
5. Add evaluator.
6. Add fixture and golden payloads.
7. Add offline tests.
8. Document boundaries.
9. Connect behind an explicit integration layer only after review.

## Avoid

- adding API routes before contract stability
- connecting to PPTX before visual blueprint stability
- using DB persistence before output versioning
- calling external AI before deterministic fixtures pass
- changing old contracts to satisfy a new module

## Recommended Adapter Rule

When a downstream module needs a different shape, create an adapter instead of mutating upstream models.
