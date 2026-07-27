# Implementation Checklist

This checklist must be used before implementation starts and at each implementation phase gate.

---

## 1. Pre-implementation

- [ ] Human approval to begin implementation is recorded.
- [ ] Existing production PPTX generator remains unchanged.
- [ ] Existing API, DB, frontend, and Beautiful.ai flows remain unchanged.
- [ ] Feature flag strategy is defined before integration.
- [ ] Blueprint schema is reviewed by engineering.
- [ ] Renderer boundary is accepted: draw only, no AI decisions.

---

## 2. Contract Checklist

- [ ] `PresentationBlueprint` JSON Schema exists.
- [ ] Component input/output schemas exist.
- [ ] Enum values are versioned.
- [ ] Unknown enum values fail validation.
- [ ] Required fields fail fast when missing.
- [ ] Numeric tokens have preservation metadata.
- [ ] Assumptions are explicitly marked.
- [ ] Human review flags are preserved.

---

## 3. Prompt Checklist

- [ ] Every AI has a System Prompt.
- [ ] Every AI has a Developer Prompt.
- [ ] Every AI has an Output JSON example.
- [ ] Every AI has a Few-shot example.
- [ ] Every AI has Temperature guidance.
- [ ] Every AI has Failure Recovery rules.
- [ ] Prompts forbid invented facts.
- [ ] Prompts forbid outputting fields owned by other components.
- [ ] Prompt versions are stored with output metadata.

---

## 4. Catalog Checklist

- [ ] Slide Catalog has at least 80 slide types.
- [ ] Diagram Catalog has at least 50 diagram types.
- [ ] Theme Catalog has all 8 required themes.
- [ ] Catalog IDs are unique.
- [ ] Deprecated IDs remain backward compatible or mapped.
- [ ] Unsupported diagrams have fallback definitions.

---

## 5. Renderer Checklist

- [ ] Renderer accepts only validated blueprint.
- [ ] Renderer does not call LLMs.
- [ ] Renderer does not rewrite text.
- [ ] Renderer does not invent values.
- [ ] Renderer creates editable PowerPoint shapes.
- [ ] Renderer preserves all numeric values.
- [ ] Renderer reports structured validation errors.
- [ ] Renderer rejects unsupported diagrams.
- [ ] Renderer flags overflow instead of silently shrinking below limits.
- [ ] Renderer emits metadata and warnings.

---

## 6. Visual QA Checklist

- [ ] PPTX opens without repair.
- [ ] No broken relationships.
- [ ] No external references unless explicitly allowed.
- [ ] No body text below 17 pt in main slides.
- [ ] No headline below 28 pt in main slides.
- [ ] No text outside safe area.
- [ ] Page numbers are present where required.
- [ ] Footer does not compete with content.
- [ ] Diagrams are editable.
- [ ] Contact sheet generated.
- [ ] Representative slides reviewed by humans.

---

## 7. Regression Checklist

- [ ] Legacy PPTX generation still passes.
- [ ] PDF generation still passes.
- [ ] Beautiful.ai generation still passes.
- [ ] Proposal generation still passes.
- [ ] Authentication tests still pass.
- [ ] Role and organization isolation tests still pass.
- [ ] Existing frontend build still passes.

---

## 8. Security Checklist

- [ ] No API keys in prompts, logs, fixtures, or blueprint output.
- [ ] No passwords or tokens in generated artifacts.
- [ ] Customer content is not written to public docs or committed fixtures.
- [ ] External asset provenance is recorded.
- [ ] No hidden external links in PPTX relationships.
- [ ] Debug artifacts are safe and local-only.

---

## 9. Human Review Checklist

- [ ] Main message is understandable in 10 seconds.
- [ ] Each slide has one primary purpose.
- [ ] Deck story is understandable from headlines alone.
- [ ] Visual type supports the message.
- [ ] Evidence and assumptions are clear.
- [ ] Proposal does not overclaim.
- [ ] Reviewer can edit the PPTX comfortably.

---

## 10. Production Adoption Checklist

- [ ] Feature flag default is off.
- [ ] Rollback is documented.
- [ ] Production trial scope is limited.
- [ ] Human visual score target is met.
- [ ] Support team knows failure modes.
- [ ] Monitoring metrics are defined.
- [ ] Adoption decision is approved by a human owner.

---

## 11. Definition of Done

Presentation Engine 2.0 can be considered production-ready only when:

- blueprint contracts are stable
- renderer remains deterministic
- visual QA passes
- human reviewers approve output quality
- legacy generation has no regression
- rollback has been tested
