# Phase3F-23A-2D dependency-gap audit

The clean branch is correctly isolated from `design-refresh` and contains only the two approved checkpoint commits before repair. The first focused run exposed three real repair areas: the Summary cap is 10, registry-referenced Native PPTX dependencies are absent, and two evidence tests use pre-22C incomplete fixtures. Four old assertions are stale: two expect 28 roles, one expects the dispatcher not to be connected, and the evidence tests use the old fixture shape.

Registry audit concludes that 29 roles is correct: 11 Summary entries, 15 Detail entries, and three conditional entries including the intentional ROADMAP role. No registry edit is justified.

The repair is limited to the one-line Summary cap, exactly the registry-referenced source/runtime PPTX files, and focused test expectations/fixtures. Provenance, sample-leak, completeness, Feature Flag, and fallback guards remain fail-closed.

No push, deployment, main change, Render/Vercel change, or `design-refresh` change is permitted in this phase.

## Post-repair result

All 29 registry roles now have present runtime assets and matching registry SHA-256 values; the 29 corresponding source trace assets also match. The minimal repair changed the Summary cap from 10 to 11, updated three stale focused-test files, and upgraded only the two drifted evidence fixtures to the current five-row contract. No registry, adapter guard, or production API contract change was made.

The focused regression passed: 88 collected, 88 passed, 0 failed. Feature Flag default remains OFF. The repair set is limited to one production code file, three focused-test files, 53 PPTX dependencies (24 newly required runtime assets plus 29 registry source assets), and these eleven audit artifacts. No unrelated files are included.
