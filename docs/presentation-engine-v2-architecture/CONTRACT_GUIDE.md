# Contract Guide

## Existing Contracts

| Contract | Owner | Purpose |
|---|---|---|
| Deck Contract | Deck Planner | deck structure and slide plan |
| Evidence Contract | Evidence Planner | proof requirements and missing evidence warnings |
| Message Contract | Message Designer | message copy and evidence disclosure |
| Slide Intent Contract | Slide Intent | abstract visual intent and reading plan |
| Alpha Integration Contract | Alpha Integration | offline cross-module validation |

## Contract Rules

- Contracts are append-only unless a new version is introduced.
- Destructive field rename is prohibited.
- Required fields should not be removed.
- New enum values require tests and documentation.
- Every contract needs fixture and golden coverage.

## Future Contracts

| Future Contract | Owner | Expected Purpose |
|---|---|---|
| Visual Plan Contract | Visual Director | visual composition and diagram/chart selection |
| Rendering Blueprint Contract | Blueprint Composer | renderer-ready object structure |
| Renderer Contract | Renderer | supported PowerPoint primitives and output metadata |

## Versioning

Current version strings should remain explicit in model fields. Future breaking changes should use a new version value and adapter.

## Compatibility

Adapters should convert old contracts to new contracts. Existing modules should not be rewritten just to satisfy a downstream change.
