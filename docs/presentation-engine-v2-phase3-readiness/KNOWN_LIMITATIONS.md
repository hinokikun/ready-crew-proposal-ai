# Known Limitations

## Current Limitations

- Visual Director Engine is not implemented.
- Visual Plan generation logic is not implemented.
- Candidate scoring is not implemented.
- Candidate ranking is not implemented.
- Visual Plan fixtures and golden outputs are not yet created.
- No runtime integration exists.
- No PPTX or renderer integration exists.

## Contract Limitations

- Phase4 composition metadata is partial.
- Audience-specific visual policy is not first-class.
- Decision stage visual policy is not first-class.
- Fallback visual is not first-class.
- Cross-slide diversity is not first-class.
- Accessibility is not first-class.

## Review Limitations

- This review is static and document-based.
- Existing test suites were not required for this review.
- No generated deck was visually inspected.
- No external AI behavior was evaluated.

## Practical Meaning

Phase3 can begin safely, but the first implementation should remain offline and
deterministic. It should not be connected to Version81 or the production PPTX
pipeline until golden quality is proven.
