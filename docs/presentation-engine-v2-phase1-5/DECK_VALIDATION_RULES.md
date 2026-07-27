# Deck Validation Rules

## Error code families

- `PE2-DECK-SCHEMA-*`
- `PE2-DECK-STRUCTURE-*`
- `PE2-DECK-NARRATIVE-*`
- `PE2-DECK-AUDIENCE-*`
- `PE2-DECK-QUALITY-*`
- `PE2-DECK-TRANSITION-*`
- `PE2-DECK-SAFETY-*`

## Main rules

- deck version must match `pe2_deck_blueprint_v1`
- section IDs must be unique
- slide blueprint IDs must be unique
- section order must be unique
- slide order must be unique
- cover should be first
- final section should be `next_action`, `closing`, or `appendix`
- required sections must exist
- executive decks require executive summary
- section slide IDs must reference planned slide blueprint IDs
- every planned slide should have a slide blueprint reference
- story arc order must not be reversed
- recommendation must not appear before diagnosis
- pricing without KPI or ROI support is flagged
- internal placeholder labels are rejected

