# Risk Analysis

This document identifies implementation and product risks for Presentation Engine 2.0.

---

## 1. Risk Summary

| ID | Risk | Severity | Probability | Impact | Mitigation |
|---|---|---:|---:|---|---|
| R001 | Renderer starts making AI-like decisions | Critical | Medium | Unstable output, untestable behavior | Renderer accepts blueprint only; no AI calls; schema validation required. |
| R002 | AI component responsibilities overlap | High | High | Conflicting decisions | Use responsibility matrix and field ownership tests. |
| R003 | Blueprint is too vague for PPTX rendering | High | Medium | Renderer cannot draw reliably | Implement JSON Schema before renderer. |
| R004 | Diagram definitions are not executable | High | Medium | Diagrams degrade into text boxes | Require nodes, connectors, groups, labels, and bounds. |
| R005 | Visual quality is subjective only | Medium | High | Hard to prove improvement | Add rubric, render inspection, and human review gates. |
| R006 | Too many slide types implemented at once | Medium | High | Scope blowup | Start with 12 core slide types, then expand. |
| R007 | Theme tokens are inconsistent | Medium | Medium | Deck feels fragmented | Implement theme validation and token inheritance. |
| R008 | Text overflow remains unresolved | High | Medium | Unusable slides | White Space Optimizer plus renderer overflow errors. |
| R009 | AI invents numbers or proof | Critical | Medium | Business and trust risk | Numeric integrity list, evidence refs, assumption labels. |
| R010 | Existing PPTX generation regresses | High | Low | Production breakage | Feature flag, isolated prototype path, regression tests. |
| R011 | External assets create licensing risk | High | Medium | Compliance risk | Require asset metadata and placeholders by default. |
| R012 | Diagrams are not editable | High | Medium | Users cannot revise deck | Use PowerPoint shapes; raster images prohibited for text and diagrams. |
| R013 | Prompt failures return partial JSON | Medium | High | Pipeline stops unpredictably | JSON repair, retries, safe fallback output. |
| R014 | Component latency becomes too high | Medium | Medium | Poor UX | Batch slide-level tasks and cache deterministic outputs. |
| R015 | Human review becomes unclear | Medium | Medium | Users approve poor strategy | Include review questions per slide and deck. |
| R016 | Theme and typography violate accessibility | Medium | Medium | Low readability | Contrast and font-size validators. |
| R017 | Catalogs become stale | Low | Medium | Inconsistent future behavior | Version catalogs and add tests for deprecated IDs. |
| R018 | Implementation ignores the design contract | High | Medium | Architecture drift | Use this review as required implementation checklist. |

---

## 2. Critical Risks

### R001 Renderer becomes AI

The renderer must not infer layout, message, diagram, or strategy. If renderer logic starts filling missing content with "reasonable defaults," the architecture becomes untestable.

Required control:

- renderer input type is only `PresentationBlueprint`
- no prompt calls inside renderer package
- no summarization or rewriting helpers
- validation errors instead of silent inference

### R009 AI invents business facts

Sales proposals often include budget, schedule, ROI, and evidence. Invented facts are unacceptable.

Required control:

- numeric tokens must be preserved
- unknown values must be marked `assumption`, `missing`, or `human_review_required`
- supporting evidence must include source references when available

---

## 3. High Risks

### Blueprint insufficiency

If the blueprint does not include safe area, typography, diagram nodes, and fallback metadata, the renderer will need to guess. This is forbidden.

Control:

- implement schema validation before rendering
- fixture all supported visual types
- define renderer failure codes

### Visual quality gap

Even with valid rendering, the deck may still look average.

Control:

- use rendered PNG inspection
- define visual quality rubric
- compare against human-approved prototypes
- require human approval before production integration

---

## 4. Regression Risks

Existing flows must remain stable:

- legacy PPTX generation
- PDF generation
- Beautiful.ai generation
- proposal generation
- quality gate
- history and admin screens

Control:

- keep Presentation Engine 2.0 behind an explicit feature flag during implementation
- do not replace existing generator until acceptance gates pass
- run current PPTX regression tests on every integration phase

---

## 5. Security and Compliance Risks

| Area | Risk | Control |
|---|---|---|
| Prompts | customer data leakage in logs | redact prompt logs |
| Assets | unlicensed image use | require asset metadata |
| Output | hidden external links | scan relationships |
| Numbers | invented ROI or cost | numeric integrity checks |
| Review | unapproved assumptions | human review required |

---

## 6. Operational Risks

| Risk | Control |
|---|---|
| High latency | batch slide processing, use deterministic rules where possible |
| Cost growth | restrict AI calls per slide, reuse upstream outputs |
| Debug difficulty | save component outputs in non-secret debug artifacts |
| Inconsistent output | version prompts, catalogs, and schemas |

---

## 7. Risk Acceptance

Implementation may begin only if:

- schema validation is implemented first
- renderer remains deterministic
- output is isolated from production by feature flag
- human visual approval remains required for production adoption
