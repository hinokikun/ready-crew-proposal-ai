# ProposalPilot V39.2 Real Proposal Validation

Status: real-project validation only. Not integrated into production PPTX generation.

## 1. Purpose

Version 39.1 proved that ProposalPilot can produce a premium, memorable, editable proposal prototype for an AI image-recognition case.

Version 39.2 validates whether the same visual system can survive real proposal variation without collapsing into:

- an AI image-recognition-only template
- a flower-auction-specific design
- a generic SaaS card deck
- an overloaded consulting document
- a layout that fails when copy or diagram structure changes

This document is the validation output. No backend, frontend, API, DB, migration, Beautiful.ai, production PPTX generation code, or proposal generation logic was changed.

## 2. Validation Scale

| Mark | Meaning |
|---|---|
| Fit | The V39.1 design pattern can be used with wording and icon changes only. |
| Adjust | The page type works, but the hero visual, diagram, labels, or KPI structure must be adapted by category. |
| Split | A category-specific template variant is required before production integration. |

## 3. Overall Finding

V39.1 is strongest for AI image recognition and AI-OCR because its signature motif is an AI recognition frame with candidate tags and human confirmation.

It is usable for RPA, CRM, AI chatbot, generated AI implementation, and internal knowledge search if the visual signature is generalized from "recognition frame" to "AI work frame."

It is weakest for Web production because the value story is less about AI candidate detection and more about content, UX, traffic, brand, CMS, operations, and conversion. Web production needs a separate visual family to avoid forcing image-recognition metaphors into a web proposal.

## 4. Project-by-project Validation Matrix

| Project | Hero | Summary | Problem | Before/After | Architecture | PoC | KPI | Estimate | Overall |
|---|---|---|---|---|---|---|---|---|---|
| AI画像認識 | Fit | Fit | Fit | Fit | Fit | Fit | Fit | Fit | High fit |
| RPA | Adjust | Fit | Fit | Fit | Adjust | Fit | Adjust | Fit | Medium-high fit |
| CRM | Adjust | Fit | Fit | Adjust | Adjust | Fit | Adjust | Fit | Medium fit |
| Web制作 | Split | Adjust | Fit | Adjust | Split | Adjust | Adjust | Adjust | Needs separate variant |
| AIチャットボット | Adjust | Fit | Fit | Fit | Adjust | Fit | Adjust | Fit | Medium-high fit |
| AI-OCR | Fit | Fit | Fit | Fit | Fit | Fit | Fit | Fit | High fit |
| 生成AI導入支援 | Adjust | Fit | Adjust | Adjust | Split | Fit | Adjust | Adjust | Medium fit |
| 社内ナレッジ検索 | Adjust | Fit | Fit | Fit | Adjust | Fit | Adjust | Fit | Medium-high fit |

## 5. Project Mock Validation

### 5.1 AI画像認識

Mock premise:

- Visual inspection, object detection, candidate classification, human confirmation, API/CSV integration, and learning loop.

Pages that work:

- Hero: recognition frame, target object, classification tags.
- Summary: AI supports human judgment.
- Problem: human inspection load accumulates.
- Before/After: AI candidate area expands, human approval remains.
- Architecture: AI Vision Engine plus Human Review UI works directly.
- PoC: data collection, annotation, model validation, field validation.
- KPI: candidate accuracy, correction rate, inspection time.
- Estimate: PoC design, data preparation, model verification, integration.

Pages needing improvement:

- None critical. Add real customer object imagery after approval.

Template note:

- This is the native source case for V39.1.

### 5.2 RPA

Mock premise:

- Manual back-office task repetition is automated through workflow bots, but exception handling and approval remain human.

Pages that work:

- Summary: "AI/automation does not remove human judgment; it removes repetitive handling."
- Problem: task queues, manual copy/paste, approval delays, exception handling.
- Before/After: human handles every operation before; bot handles standard operations after.
- PoC: target process selection, exception analysis, bot verification, operation test.
- Estimate: process discovery, bot design, integration, operation support.

Pages needing improvement:

- Hero: recognition frame should become "Automation Control Frame" around a task queue, not an image target.
- Architecture: AI Vision Engine should become "Automation Orchestration Layer."
- KPI: candidate accuracy is irrelevant. Use processing time, exception rate, manual touch count, rework count, bot success rate.

Template note:

- Requires a workflow-lane variant with queue, rule engine, bot execution, exception review, and audit log.

### 5.3 CRM

Mock premise:

- Sales activities, customer history, opportunity status, next actions, and reporting are unified.

Pages that work:

- Summary: CRM strengthens sales judgment by organizing relationship and opportunity data.
- Problem: customer history fragmentation, follow-up leakage, pipeline opacity.
- PoC: field adoption, data migration check, role-based operation, reporting validation.
- Estimate: requirements, data preparation, configuration, integration, training.

Pages needing improvement:

- Hero: AI recognition visual is too image-specific. Use "Customer 360 workspace" as the main visual.
- Before/After: should emphasize fragmented tools to unified customer timeline, not AI candidate detection.
- Architecture: should show customer data, activity history, pipeline, notification, analytics, and permission layers.
- KPI: use follow-up completion rate, pipeline update rate, proposal conversion, activity visibility, data completeness.

Template note:

- Needs a customer-data operating model variant.

### 5.4 Web制作

Mock premise:

- Website renewal, structure, design, CMS, content, SEO, conversion path, and operations.

Pages that work:

- Problem: current-site issues, outdated information, mobile usability, conversion friction can be shown as a flow.

Pages needing improvement:

- Hero: AI recognition frame does not fit. A site map, viewport mock, brand system, or customer journey should be the visual lead.
- Summary: "AI supports human judgment" is not always the central message. The central message should be "site experience and operations are redesigned together."
- Before/After: should show current site to renewed experience, not AI vs human work allocation.
- Architecture: should show CMS, content, forms, analytics, hosting, operations, and security.
- PoC: Web projects often need discovery, information architecture, design, build, test, release. PoC language may be wrong unless the case is experimental.
- KPI: inquiry rate, mobile usability, content freshness, page speed, conversion, recruitment entry rate.
- Estimate: design, content, CMS, development, testing, release, operation.

Template note:

- Needs a separate web-production variant. Do not force V39.1's AI recognition motif into web proposals.

### 5.5 AIチャットボット

Mock premise:

- Customer or employee inquiries are answered by a chatbot with escalation to human operators and continuous improvement from unresolved questions.

Pages that work:

- Summary: AI answers routine questions while humans handle exceptions.
- Problem: inquiry concentration, answer inconsistency, response delay, knowledge update burden.
- Before/After: manual response queue becomes bot-first with escalation.
- PoC: FAQ corpus, intent design, answer validation, escalation testing, field trial.
- Estimate: knowledge preparation, bot configuration, integration, evaluation, operation.

Pages needing improvement:

- Hero: recognition frame should become "Conversation Understanding Frame" around a chat panel.
- Architecture: AI Vision Engine should become "Conversation Engine" with knowledge base, guardrails, escalation, and logs.
- KPI: answer resolution rate, escalation rate, response time, operator workload, satisfaction, hallucination incident count.

Template note:

- Needs a conversation UI variant with message bubbles, intent tags, escalation path, and knowledge feedback loop.

### 5.6 AI-OCR

Mock premise:

- Documents are read by OCR, extracted fields are suggested, humans confirm exceptions, and results are sent to business systems.

Pages that work:

- Hero: recognition frame can wrap document areas instead of products.
- Summary: AI extracts candidates; humans confirm low-confidence or exception fields.
- Problem: manual transcription, entry mistakes, format variance, verification burden.
- Before/After: full manual entry moves to extraction plus confirmation.
- Architecture: document input, OCR engine, field extraction, confidence score, human review, API/CSV integration.
- PoC: document sample check, field definition, accuracy validation, exception operation.
- KPI: field extraction accuracy, correction rate, processing time, exception rate, throughput.
- Estimate: PoC design, document preparation, OCR verification, UI/integration, operation.

Pages needing improvement:

- Minimal. Flower/product labels must be replaced by document field tags.

Template note:

- V39.1 can generalize well if recognition tags become field extraction tags.

### 5.7 生成AI導入支援

Mock premise:

- Internal work is improved through prompt design, retrieval, workflow integration, governance, and training.

Pages that work:

- Summary: AI assists workers but humans keep final responsibility.
- PoC: use case selection, data boundary, prompt validation, security review, operation trial.

Pages needing improvement:

- Hero: image recognition is not appropriate. Use "AI workbench" or "knowledge-assisted task cockpit."
- Problem: scattered work instructions, repetitive drafting, review burden, governance risk, tool adoption variance.
- Before/After: should show work process plus AI assist points, not object recognition.
- Architecture: needs LLM, retrieval, guardrails, prompt templates, audit log, permission, human review.
- KPI: task time reduction, review correction rate, reuse rate, policy violation count, user adoption, answer usefulness.
- Estimate: use case design, prompt/template creation, governance, integration, training, operation.

Template note:

- Needs a governance-heavy AI assistant variant. The learning loop is still useful, but visual lead must shift from recognition to assisted-work cockpit.

### 5.8 社内ナレッジ検索

Mock premise:

- Internal documents, manuals, FAQ, project history, and procedures are searched through AI-assisted retrieval with source grounding and feedback.

Pages that work:

- Summary: AI helps employees find relevant information while humans confirm applicability.
- Problem: scattered documents, outdated files, search time, answer inconsistency, dependency on experts.
- Before/After: manual document hunting becomes AI-assisted retrieval with source confirmation.
- PoC: data inventory, source permission check, retrieval quality validation, user trial.
- Estimate: data preparation, search setup, access control, evaluation, operation.

Pages needing improvement:

- Hero: recognition frame should become "Knowledge Retrieval Frame" around document/source cards.
- Architecture: should show content sources, index, retrieval engine, answer UI, citation/source confirmation, feedback loop.
- KPI: search success rate, time to answer, source citation rate, unresolved question rate, content freshness.

Template note:

- Needs a knowledge-retrieval variant with source cards, citation tags, and feedback loop.

## 6. Page-type Validation

| Page type | Common template potential | Category-specific risk | Version40 action |
|---|---|---|---|
| Hero | Medium | High. The main visual must change by category. | Create category-specific hero visual modules. |
| Summary | High | Low. Human-centered AI message works broadly. | Keep common structure with category-specific central sentence. |
| Problem | High | Medium. Workflow differs but bottleneck map works. | Use configurable process steps and pain tags. |
| Before/After | High | Medium. Assignment of AI, automation, system, and human changes. | Build role-band variants: AI assist, automation, system consolidation, web renewal. |
| Architecture | Medium | High. Engine labels and layers vary significantly. | Create architecture families by category. |
| PoC | High | Low to medium. Most transformation proposals need phased validation. | Keep common gate roadmap, change phase labels. |
| KPI | Medium | High. KPI names and measurement states vary. | Use category KPI packs. |
| Estimate | Medium | High. Cost items must be category-specific. | Use category estimate item packs. |

## 7. Common Template Parts

These can become production-ready shared components in Version40:

1. ProposalPilot footer, page number, and section label.
2. Dark impact page and light explanation page rhythm.
3. One-visual-lead rule per slide.
4. Human-in-the-loop message pattern.
5. Problem bottleneck map structure.
6. Before/After role-band structure.
7. Six-gate PoC roadmap.
8. KPI dashboard shell with status chips.
9. Scope gate / next action closing page.
10. Editable PowerPoint-native tags, cards, connectors, and UI pieces.

## 8. Category-specific Template Needs

### 8.1 Hero Visual Families

| Category | Hero visual should be |
|---|---|
| AI画像認識 | Object/image recognition frame |
| AI-OCR | Document field extraction frame |
| RPA | Task queue and automation control panel |
| CRM | Customer 360 and pipeline workspace |
| Web制作 | Website viewport, journey, site map, or brand experience |
| AIチャットボット | Conversation UI with intent and escalation tags |
| 生成AI導入支援 | AI workbench with prompt, retrieval, guardrail, and review zones |
| 社内ナレッジ検索 | Knowledge retrieval frame with source cards and citations |

### 8.2 Architecture Families

| Family | Applies to | Required layers |
|---|---|---|
| Recognition / Extraction | AI画像認識, AI-OCR | Input, AI extraction, confidence, human review, integration, learning |
| Automation Workflow | RPA | Trigger, bot execution, exception handling, approval, audit |
| Business Data Platform | CRM | Customer data, activity, pipeline, workflow, analytics, permissions |
| Digital Experience | Web制作 | Content, UX, CMS, forms, analytics, hosting, operations |
| Conversation AI | AIチャットボット | Channel, intent, knowledge, guardrail, escalation, logs |
| Generative AI Workbench | 生成AI導入支援 | Use case, prompt/template, retrieval, policy, review, audit |
| Knowledge Retrieval | 社内ナレッジ検索 | Sources, indexing, retrieval, answer UI, citation, feedback |

### 8.3 KPI Packs

| Category | KPI examples |
|---|---|
| AI画像認識 | Candidate accuracy, correction rate, inspection time, classification variance |
| AI-OCR | Field extraction accuracy, exception rate, manual correction count, throughput |
| RPA | Manual touch count, bot success rate, exception rate, processing time |
| CRM | Pipeline update rate, follow-up completion, data completeness, conversion visibility |
| Web制作 | Inquiry conversion, mobile usability, content freshness, page speed |
| AIチャットボット | Resolution rate, escalation rate, response time, answer usefulness |
| 生成AI導入支援 | Reuse rate, task time, review correction rate, governance incident count |
| 社内ナレッジ検索 | Search success, source citation rate, time to answer, unresolved rate |

### 8.4 Estimate Packs

| Category | Estimate item examples |
|---|---|
| AI画像認識 | Data preparation, annotation, model verification, review UI, integration |
| AI-OCR | Document analysis, field definition, OCR validation, exception UI, integration |
| RPA | Process discovery, bot design, exception handling, test operation, monitoring |
| CRM | Data migration, configuration, workflow setup, reporting, training |
| Web制作 | IA/design, content, CMS, frontend/backend build, testing, release |
| AIチャットボット | Knowledge preparation, scenario design, bot build, escalation, operation |
| 生成AI導入支援 | Use case design, prompt templates, governance, training, integration |
| 社内ナレッジ検索 | Document inventory, indexing, permission design, retrieval tuning, operation |

## 9. Risks Found

| Risk | Severity | Detail | Mitigation for Version40 |
|---|---|---|---|
| AI recognition motif is too image-specific | High | RPA, CRM, Web, chatbot, GenAI, and knowledge search should not all look like image recognition. | Generalize into category-specific "AI work frame" variants. |
| Architecture page may become misleading | High | AI Vision Engine label only fits recognition/extraction projects. | Add architecture family selector. |
| KPI dashboard can imply unsupported numbers | High | Premium visuals may tempt large invented metrics. | Keep "PoCで測定/確定/合意" states unless real values exist. |
| Estimate page can become generic | High | Each category requires different cost items. | Use estimate packs tied to project category. |
| Web production proposal does not fit V39.1 | High | Web projects need UX/CMS/content/conversion story. | Build separate Digital Experience visual variant. |
| Hero page quality depends heavily on category asset | Medium | Some categories lack obvious visual object. | Provide abstract hero modules per category. |
| Before/After role bands need category semantics | Medium | "AI vs human" is not always the change. | Support role types: human, AI, automation, system, customer, governance. |
| UI mock may become decorative | Medium | Generic UI panels without domain-specific controls lose trust. | Require category-specific UI controls and labels. |
| PoC wording may not fit all sales cases | Medium | Web制作 and CRM may be implementation projects rather than PoC-first. | Allow "導入計画" roadmap variant. |
| ProposalPilot signature may overpower customer context | Low | Cyan tags and frames can feel samey if overused. | Limit signature motif to 2-4 pages per deck. |

## 10. Version40 Production Integration Notes

Before production integration, Version40 should implement a presentation category selector that chooses:

1. Hero visual family.
2. Problem workflow steps.
3. Before/After role-band model.
4. Architecture family.
5. KPI pack.
6. Estimate pack.
7. PoC or implementation roadmap variant.
8. Category-specific icon set.

The production engine should not simply reuse the AI image-recognition V39.1 deck and replace text. That would produce plausible but misleading proposals for CRM, Web production, generated AI consulting, and knowledge search.

## 11. Priority Fixes Before Version40 Integration

### Priority A: must fix before production integration

1. Generalize the AI Recognition Frame into category-specific AI Work Frames.
2. Add architecture family variants instead of using AI Vision Engine everywhere.
3. Add KPI packs by category and prohibit unsupported actual values.
4. Add estimate item packs by category.
5. Create a separate Web制作 / Digital Experience visual variant.
6. Ensure all category labels replace flower/image-specific terminology.

### Priority B: should fix during Version40 implementation

1. Add category-specific icon sets while preserving ProposalPilot style.
2. Add roadmap variants: PoC, implementation, rollout, migration, and training.
3. Add validation rules for maximum text length per page type.
4. Add per-category UI mock modules.
5. Add category-specific forbidden-term checks to prevent template leakage.
6. Add visual QA checks for repeated layouts and overused signature motifs.

### Priority C: can follow after Version40

1. Add customer industry color accents within brand limits.
2. Add optional customer-logo and real-image placeholders.
3. Add appendix page variants for technical details.
4. Add per-category sales talk-track notes.
5. Add reviewer scoring sheet for human visual approval.

## 12. Final Judgment

V39.1 is strong enough as a design direction, but not yet safe as a universal production template.

It should be treated as:

- Approved visual direction for AI image recognition and AI-OCR.
- Adaptable base for RPA, AI chatbot, and knowledge search.
- Partial base for CRM and generated AI implementation support.
- Not suitable as-is for Web production.

Version40 should integrate the visual system, not the single V39.1 deck structure.

Production integration should wait until category-specific hero, architecture, KPI, and estimate variants are defined and tested.
