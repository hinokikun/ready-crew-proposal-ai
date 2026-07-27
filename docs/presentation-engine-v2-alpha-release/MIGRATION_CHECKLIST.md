# Migration Checklist

## Version81 Integration Preconditions

- [ ] Phase3 Visual Director is implemented offline only.
- [ ] Visual Director produces valid Visual Plan Contract for golden cases.
- [ ] Phase4 Blueprint Composer is implemented offline only.
- [ ] Blueprint Composer preserves message and evidence semantics.
- [ ] Phase5 Renderer produces editable PowerPoint output.
- [ ] Renderer does not rewrite strategy, evidence, or message.
- [ ] Human review approves visual quality.
- [ ] Feature flag design is complete.
- [ ] Legacy PPTX generation remains default.
- [ ] Rollback path returns to legacy generator without data migration.

## Contract Compatibility Checklist

- [ ] Existing Deck Blueprint contract remains versioned.
- [ ] Existing Evidence Planner contract remains versioned.
- [ ] Existing Message Designer contract remains versioned.
- [ ] Existing Slide Intent contract remains versioned.
- [ ] Visual Plan Contract is append-only or versioned.
- [ ] Breaking changes use adapters, not destructive edits.

## Runtime Safety Checklist

- [ ] No DB migration required for first pilot.
- [ ] No API behavior changes without feature flag.
- [ ] No frontend default behavior changes without feature flag.
- [ ] No OpenAI dependency required for deterministic fallback.
- [ ] No Beautiful.ai dependency required for local validation.
- [ ] No production PPTX behavior changes when feature flag is off.

## Testing Checklist

- [ ] Contract tests pass.
- [ ] Schema tests pass.
- [ ] Validator tests pass.
- [ ] Golden tests pass.
- [ ] Cross-module integration tests pass.
- [ ] Legacy proposal generation regression passes.
- [ ] Existing PPTX/PDF/Beautiful.ai regression passes.

## Human Review Checklist

- [ ] Sales story is coherent.
- [ ] Evidence is visible and not invented.
- [ ] Visual plan is customer-facing.
- [ ] Executive decks are concise.
- [ ] Technical decks are detailed enough.
- [ ] No unsupported chart is generated.
- [ ] No PowerPoint output is connected until visual quality is approved.

## Migration Decision

Do not connect Presentation Engine 2.0 to Version81 production flow until all
items above are reviewed and a feature-flagged rollout plan is approved.
