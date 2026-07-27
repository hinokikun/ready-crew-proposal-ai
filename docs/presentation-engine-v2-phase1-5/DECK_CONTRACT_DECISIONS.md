# Deck Contract Decisions

## Version

Supported version:

```text
pe2_deck_blueprint_v1
```

Both `deck_blueprint_version` and `schema_version` use this value.

## Reference strategy

Phase 1.5 adopts `slide_blueprint_refs` as the safe default.

Deck Blueprint references Slide Blueprint by:

- `slide_blueprint_id`
- `slide_id`
- `slide_order`
- `expected_slide_type`
- `expected_slide_goal`
- `section_id`

Embedding a full Phase 1 `SlideBlueprint` is allowed but optional. References are preferred for fixtures and contract tests.

## Non-goals

Deck Blueprint must not contain:

- font size
- shape coordinates
- detailed diagram layout
- renderer-only metadata
- generated customer facts

