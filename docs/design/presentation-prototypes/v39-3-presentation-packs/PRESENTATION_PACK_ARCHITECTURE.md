# ProposalPilot Presentation Pack Architecture

Status: design approval specification only. Not integrated into production PPTX generation.

## 1. Design Goal

ProposalPilot should not use one universal slide layout for every proposal category. Version 39.2 proved that the V39.1 visual system works well for AI image recognition and AI-OCR, but needs category-specific variants for RPA, CRM, chatbot, knowledge search, generative AI, and web production.

Version 39.3 defines a three-layer architecture so the production PPTX engine can select a visual expression by project category without losing ProposalPilot brand consistency.

## 2. Three-layer Structure

| Layer | Name | Responsibility | Input | Output | Can change | Must not contain |
|---|---|---|---|---|---|---|
| Layer 1 | Core Presentation System | Brand, typography, rhythm, quality rules, editability | Deck metadata, page type, brand tokens | Common slide shell and QA rules | Colors within brand, spacing, footer, tags, connectors | Category-specific claims or fixed business terms |
| Layer 2 | Category Presentation Pack | Category-specific hero, architecture, KPI, estimate, icons, UI mock | Project category, business domain, proposal type | Pack-specific slide modules | Visual lead, data flow, KPI names, estimate items | Terms from unrelated packs |
| Layer 3 | Project-Specific Adaptation | Adapt selected pack to the actual customer case | Customer problem, constraints, budget, schedule, deliverables | Final proposal content | Titles, process labels, scope, actual facts | Unsupported numbers, secret data, irrelevant templates |

## 3. Layer 1: Core Presentation System

Core contains only reusable presentation rules:

- 16:9 slide size.
- ProposalPilot brand colors: deep navy, royal blue, cyan, white, pale blue, cool gray.
- Consistent title hierarchy.
- ProposalPilot footer and page number.
- Section labels and pack labels.
- Wide margins and non-crowded visual composition.
- Editable PowerPoint-native shapes and text.
- No external references.
- One page, one message.
- 3-second visual lead and 10-second comprehension rules.
- Overflow prevention.
- No invented metrics or unsupported target values.
- No win probability.
- No secret, API key, token, password, or customer-confidential body text.

Core does not decide whether a slide is Vision/OCR, CRM, Web, RPA, or Generic. That belongs to Layer 2.

## 4. AI Work Frame Generalization

V39.1 used an AI Recognition Frame. Version 39.3 generalizes it into the AI Work Frame.

AI Work Frame visualizes the work performed by AI, automation, system, or digital operations. It is not always an image-recognition frame.

Common conceptual flow:

1. Input
2. Processing / Work
3. Candidate / Result
4. Human Decision
5. System Integration
6. Learning / Feedback

Category mapping:

| Pack | Input | Work | Result | Human decision | Integration | Feedback |
|---|---|---|---|---|---|---|
| Vision / OCR | Image, document, form | Recognition, OCR, extraction | Candidate, field, confidence | Confirm, correct, approve | API, CSV, business system | Relearning, error log |
| Automation | Trigger, task queue | Bot execution, rule processing | Completed step, exception | Exception review | Audit log, scheduler | Rule improvement |
| Conversational AI | Question, inquiry | Search, generate, route | Answer candidate | Escalation, approval | Chat channel, ticket | Conversation log |
| Knowledge AI | Search request | Retrieval, ranking, grounding | Answer and source | Applicability check | Document platform | Feedback and freshness |
| CRM | Customer information | Analysis, scoring, next-action suggestion | Action candidate | Sales rep decision | CRM workflow | Activity history |
| Generative AI | Business input | LLM generation and template use | Draft output | Review and approve | Work environment | Prompt and policy learning |
| Digital Experience | User need | Experience design and production | Screen, journey, content | Business approval | CMS, analytics | Measurement loop |
| Generic | Current facts | Analysis and option design | Recommendation | Decision | Execution plan | Retrospective |

## 5. Category Presentation Packs

### Pack A: Vision / OCR Pack

- Applies to: AI image recognition, AI-OCR, document extraction, inspection support.
- Does not apply to: CRM, web production, generic consulting without extraction work.
- Hero lead: object or document inside a recognition/extraction frame.
- Problem diagram: manual inspection, transcription, confirmation, and exception load.
- Before / After: manual check becomes AI candidate plus human confirmation.
- Architecture: input, recognition/OCR engine, confidence, human review, integration, learning.
- PoC plan: sample data, annotation or field definition, model/OCR validation, field trial.
- KPI: candidate accuracy, read accuracy, correction rate, confirmation time, error registration rate.
- Estimate: evaluation design, data preparation, AI validation, review UI, integration, operation.
- Recommended icons: image, document, scan frame, field, confidence, human check.
- Recommended UI mock: candidate list, confidence labels, correction state.
- Prohibited: CMS, site map, pipeline update, chatbot escalation unless explicitly combined.

### Pack B: Automation Pack

- Applies to: RPA, workflow automation, back-office automation.
- Does not apply to: visual inspection, web renewal, CRM-only projects.
- Hero lead: task queue and automation control panel.
- Problem diagram: repetitive manual steps, waiting, rework, exceptions.
- Before / After: all-human operation becomes bot execution plus exception review.
- Architecture: trigger, bot orchestrator, scenario, exception desk, audit log, monitoring.
- PoC plan: process discovery, rule definition, exception analysis, trial operation.
- KPI: automation count, success rate, exception rate, processing time, manual work reduction.
- Estimate: business analysis, automation design, scenario implementation, exception handling, monitoring.
- Recommended icons: queue, bot, trigger, exception, log, monitor.
- Recommended UI mock: queue state, bot run status, exception list.
- Prohibited: recognition frame, OCR confidence, site map, customer pipeline unless combined.

### Pack C: Conversational AI Pack

- Applies to: AI chatbot, inquiry response, customer support automation.
- Does not apply to: OCR, RPA-only process automation, CRM-only projects.
- Hero lead: conversation panel with intent, source, and escalation status.
- Problem diagram: inquiry concentration, answer inconsistency, waiting, escalation gap.
- Before / After: manual response queue becomes AI answer candidate plus escalation.
- Architecture: channel, conversation engine, knowledge and guardrail, escalation desk, conversation log.
- PoC plan: inquiry collection, answer design, validation, escalation test, trial operation.
- KPI: self-resolution rate, escalation rate, answer quality, response time, user satisfaction.
- Estimate: conversation design, knowledge preparation, AI build, channel integration, operation improvement.
- Recommended icons: chat, intent, knowledge, guardrail, operator, ticket.
- Recommended UI mock: chat bubbles, answer candidate, escalation panel.
- Prohibited: OCR field extraction, site map, CRM action score unless combined.

### Pack D: Knowledge AI Pack

- Applies to: internal knowledge search, RAG, document search, source-grounded answer systems.
- Does not apply to: website renewal, RPA-only tasks, CRM-only reporting.
- Hero lead: search request connected to grounded answer and source cards.
- Problem diagram: scattered documents, search time, outdated content, expert dependency.
- Before / After: manual document hunting becomes AI-assisted retrieval with source confirmation.
- Architecture: document sources, index/retrieval, grounded answer, source review, feedback log.
- PoC plan: document inventory, permission check, retrieval validation, user trial.
- KPI: search success rate, source citation rate, answer precision, search time, usage rate.
- Estimate: document investigation, data preparation, search platform, UI, permission and operation.
- Recommended icons: document, search, source, citation, feedback.
- Recommended UI mock: search result, source cards, answer confidence.
- Prohibited: product image labels, CMS, sales pipeline unless combined.

### Pack E: CRM / Sales Intelligence Pack

- Applies to: CRM, sales support, customer analytics, sales action recommendation.
- Does not apply to: OCR extraction, RPA-only, website production.
- Hero lead: customer 360 workspace and next-action candidate.
- Problem diagram: customer history fragmentation, update leakage, pipeline opacity.
- Before / After: scattered sales records become unified customer/action workflow.
- Architecture: customer data, sales intelligence, action suggestion, manager review, CRM workflow.
- PoC plan: data model check, role-based workflow, adoption test, reporting validation.
- KPI: input rate, activity visibility, opportunity update rate, action execution rate, information quality.
- Estimate: business requirements, data design, CRM setup, external integration, adoption support.
- Recommended icons: customer, activity, pipeline, action, manager, dashboard.
- Recommended UI mock: customer card, opportunity board, action list.
- Prohibited: OCR confidence, site map, bot answer unless combined.

### Pack F: Generative AI Transformation Pack

- Applies to: generative AI implementation support, internal AI use, AI workbench setup.
- Does not apply to: pure web production, OCR-only extraction, CRM-only configuration.
- Hero lead: AI workbench where business input becomes draft output and human review.
- Problem diagram: drafting load, inconsistent review, governance risk, low reuse.
- Before / After: individual work becomes AI-assisted work with review and governance.
- Architecture: use case, LLM workbench, prompt/guardrail, review and approval, usage log.
- PoC plan: use-case selection, policy boundary, prompt validation, training, field trial.
- KPI: usage rate, work time, output adoption, revision volume, risk detection count.
- Estimate: use-case design, guideline, PoC, usage environment, education, governance.
- Recommended icons: prompt, model, guardrail, review, education, audit.
- Recommended UI mock: input, generated draft, review checklist, policy indicator.
- Prohibited: flower/image labels, CMS, pipeline update unless combined.

### Pack G: Digital Experience Pack

- Applies to: web production, web renewal, UX improvement, EC, content and measurement design.
- Does not apply to: OCR, RPA, chatbot-only, CRM-only projects.
- Hero lead: user journey, viewport mock, information architecture, or experience map.
- Problem diagram: user journey bottlenecks, outdated content, weak measurement, operation burden.
- Before / After: current site and operation become redesigned experience plus measurement loop.
- Architecture: user journey, UX/IA, design/CMS, content operation, analytics.
- PoC or plan: discovery, information architecture, design, build, test, release, operation.
- KPI: conversion-related metrics, drop-off, circulation, page speed, operation update efficiency, inquiry.
- Estimate: research/strategy, UX/IA, design, development, CMS, content, operation/measurement.
- Recommended icons: page, device, journey, CMS, analytics, content.
- Recommended UI mock: device frames, site map, journey flow, CMS operation panel.
- Prohibited: recognition frame, OCR confidence, product classification, annotation unless explicitly AI add-on.

### Pack H: Generic Consulting Pack

- Applies to: unclear category, mixed consulting, business improvement where no technical category dominates.
- Does not apply to: cases with clear Vision/OCR, RPA, CRM, Web, chatbot, GenAI, or Knowledge AI dominance.
- Hero lead: decision map and current-to-future pathway.
- Problem diagram: fragmented issues and priority ambiguity.
- Before / After: current state becomes organized target state and execution roadmap.
- Architecture: current state, analysis core, solution options, decision board, execution plan.
- Roadmap: discovery, option design, decision, execution, adoption.
- KPI: progress, quality, workload, adoption, decision criteria.
- Estimate: research, design, execution support, adoption, improvement.
- Recommended icons: map, priority, decision, roadmap, execution.
- Recommended UI mock: decision board and issue map, not a specific system UI.
- Prohibited: unconditional AI, OCR, RPA, CRM, Web, chatbot, CMS, image-recognition terms.

## 6. Architecture Pack Definitions

| Architecture | Left side | Center lead | Right side | Operations layer | Human involvement | External integration | Security / operation expression |
|---|---|---|---|---|---|---|---|
| Vision / OCR | Images, documents, forms | Recognition/OCR engine and confidence | Review UI and business system | error log, relearning | confirm fields/candidates | API, CSV, core system | audit, correction history |
| Automation | Trigger, queue, schedule | Bot orchestrator and rule scenario | exception desk and logs | monitoring, retry | exception review | job scheduler, workflow system | audit log, run status |
| Conversational AI | Chat channel, inquiry | conversation engine and knowledge | escalation, ticket, channel | conversation log | escalation and approval | chat, help desk, CRM | guardrail, source policy |
| Knowledge / RAG | document sources | retrieval and grounded answer | source review and answer UI | freshness and feedback | applicability check | document platform, SSO | permission, citation, access log |
| CRM | customer and activity data | sales intelligence and action candidate | CRM workflow and manager view | activity history | sales decision and manager review | CRM, calendar, email | role, audit, data quality |
| Generative AI | business input and use cases | LLM workbench and templates | reviewed output and usage | prompt/version log | review and approval | internal tools | policy, guardrail, audit |
| Digital Experience | user journey and content | UX/IA and design/CMS | analytics and operations | measurement loop | business approval and content operation | CMS, forms, analytics | accessibility, release operation |
| Generic | current state facts | analysis and options | decision board and execution plan | retrospective | decision and prioritization | varies by case | assumptions and risk log |

## 7. Production Implementation Assumption

A future implementation should model packs as data, not hardcoded slide text. A possible structure is:

```text
presentation_packs/
  core/
    tokens
    typography
    qa_rules
    shared_components
  packs/
    vision_ocr
    automation
    conversational_ai
    knowledge_ai
    crm
    generative_ai
    digital_experience
    generic
```

Each pack should expose:

- `pack_id`
- `applies_to`
- `hero_module`
- `problem_module`
- `before_after_module`
- `architecture_module`
- `roadmap_module`
- `kpi_pack`
- `estimate_pack`
- `term_rules`
- `qa_rules`

This document is only a design specification. No production implementation was performed.
