# Decision Rules

Version: 40.0
Status: Design only. No production implementation.

## 1. Purpose

Decision Rules define how Proposal Strategy Engine should choose:

- Strategy
- Story Pack
- Presentation Pack
- Persona Pack
- KPI Pack
- Estimate Pack
- prohibited terms

These rules are specifications only. They are not implemented in production.

## 2. Input Signals

| Signal group | Examples |
|---|---|
| Project category | AI-OCR, RPA, CRM, Web, Generative AI, Knowledge Search |
| Business objective | cost reduction, speed, quality, customer experience, governance |
| Audience terms | CEO, executive, manager, field, IT, quality, sales |
| Deliverables | PoC, MVP, full implementation, operation support, training |
| Risk terms | security, compliance, audit, accuracy, downtime, exception |
| Evidence terms | current volume, processing time, error rate, budget, schedule |
| Integration terms | API, CSV, DB, CRM, ERP, SSO, data warehouse |

## 3. Strategy Selection

| Rule | Condition | Primary Strategy |
|---|---|---|
| S1 | cost, labor, ROI, budget approval are dominant | ROI重視 |
| S2 | manual process, workload, waiting, re-entry are dominant | 業務改善重視 |
| S3 | inspection, accuracy, defects, rework, standards are dominant | 品質改善重視 |
| S4 | compliance, continuity, security, audit are dominant | リスク低減 |
| S5 | data integration, cross-department, modernization are dominant | DX推進 |
| S6 | AI model, prediction, recognition, generation are core | AI活用 |
| S7 | customer journey, brand, conversion, sales response are dominant | 顧客体験 / 競争優位 |
| S8 | deadline, backlog, launch timing are dominant | スピード重視 |

## 4. Persona Selection

| Rule | Condition | Persona |
|---|---|---|
| P1 | investment approval, board, strategy, company-wide | CEO or Executive |
| P2 | department issue, operational KPI, budget owner | Department Director |
| P3 | team process, daily operation, schedule management | Manager |
| P4 | workflow burden, usability, exceptions | Field Lead |
| P5 | API, DB, security, integration, infrastructure | Information Systems |
| P6 | quality standard, inspection, traceability | Quality Assurance |
| P7 | customer, opportunity, proposal, follow-up, pipeline | Sales |

## 5. Story Pack Selection

| Rule | Strategy | Persona | Story Pack |
|---|---|---|---|
| T1 | ROI重視 | CEO / Executive | ROI Story |
| T2 | DX推進 | Executive / Director / IT | DX Story |
| T3 | AI活用 | Director / Field / IT | AI Story |
| T4 | 業務改善重視 | Manager / Field | Automation Story |
| T5 | 品質改善重視 | QA / Field / Director | Quality Story |
| T6 | 顧客体験 / 競争優位 | Sales / Director / Executive | Customer Experience Story |

## 6. Presentation Pack Selection

Presentation Pack selection should reuse Version 39.3 Pack Selection Rules.

| Signal | Pack |
|---|---|
| image recognition, OCR, extraction, inspection | Vision / OCR |
| RPA, workflow automation, bots, exception | Automation |
| chatbot, inquiry, conversation, escalation | Conversational AI |
| RAG, knowledge search, source, citation | Knowledge AI |
| CRM, pipeline, sales activity, customer data | CRM / Sales Intelligence |
| LLM, prompt, generation, AI workbench | Generative AI Transformation |
| website, UX, CMS, EC, conversion | Digital Experience |
| no strong category | Generic Consulting |

## 7. Conflict Resolution

| Conflict | Resolution |
|---|---|
| Strong category but weak strategy | Use category pack; use Generic or ROI story depending on audience. |
| Strong strategy but unclear category | Use Generic Consulting Pack and selected story. |
| Executive audience with technical project | Start with value and risk; move architecture later. |
| Field audience with executive sponsor | Start with operation; include business summary early but brief. |
| Compound project | Select primary pack by core value, secondary pack by downstream operation. |

## 8. Prohibited Term Rules

If a category is not selected, category-specific terms must not be injected.

| Selected pack | Prohibited if not present in input |
|---|---|
| Vision / OCR | SEO, CMS, site map, conversion, CRM pipeline |
| Automation | OCR accuracy, chatbot response, CMS, SEO |
| Conversational AI | OCR, RPA bot, CMS, site map |
| Knowledge AI | CRM pipeline, CMS, OCR, bot execution |
| CRM | OCR, CMS, site map, RPA bot |
| Generative AI | OCR, CMS, CRM pipeline unless explicit |
| Digital Experience | OCR, RPA, CRM pipeline unless explicit |
| Generic Consulting | AI, OCR, RPA, CRM, chatbot, CMS, SEO unless explicit |

## 9. Fallback Rules

When confidence is low:

```text
Use Generic Consulting Pack
Use safe generic story
Do not invent category terms
Ask human review before production use
```

## 10. Decision Output

```json
{
  "strategy": "quality_improvement",
  "story_pack": "quality_story",
  "persona_pack": "quality_assurance",
  "presentation_pack": "vision_ocr",
  "kpi_pack": "quality_measurement",
  "estimate_pack": "poc_to_implementation",
  "confidence": 0.82,
  "decision_reasons": [
    "input mentions inspection",
    "input mentions classification accuracy",
    "input mentions human confirmation"
  ],
  "prohibited_terms": ["SEO", "CMS", "site map"],
  "human_review_required": false
}
```

## 11. Human Override

Future production implementation should allow manager or admin review to override:

- strategy
- story pack
- persona pack
- primary presentation pack
- secondary presentation pack

Override must be logged when implemented.
