# Deck Normalization Rules

Allowed safe normalization:

- trim whitespace
- normalize line endings
- normalize enum display labels
- remove duplicate primitive list items
- generate deterministic `deck_id` when missing
- set `deck_blueprint_version` when missing
- set `schema_version` when missing
- fill missing `section_order` from current section order
- fill missing `slide_order` from current slide order
- calculate `target_slide_count` from slide plan if missing

Forbidden:

- adding missing sections
- deleting slides
- changing story
- changing audience
- generating CTA
- inventing facts
- changing slide order without explicit input

