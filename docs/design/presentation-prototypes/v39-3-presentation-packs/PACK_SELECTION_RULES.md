# ProposalPilot Pack Selection Rules

Status: specification only. No production classification code implemented.

## 1. Selection Inputs

The future production engine should consider:

- Project title
- Project summary
- Customer problem
- Proposed solution
- Deliverables
- Integration targets
- KPI text
- Budget constraints
- Schedule
- Industry and department
- User-selected category if provided

## 2. Selection Output

The selector should return:

```json
{
  "primary_pack": "vision_ocr",
  "secondary_pack": "automation",
  "confidence": 0.86,
  "selection_reasons": ["帳票", "読取精度", "RPA連携"],
  "prohibited_terms": ["CMS", "サイトマップ"],
  "required_slide_types": ["Hero", "Problem", "BeforeAfter", "Architecture", "KPI", "Estimate"],
  "optional_slide_types": ["Risk", "Appendix"]
}
```

## 3. Pack Signals

| Pack | Strong signals | Weak or ambiguous signals |
|---|---|---|
| Vision / OCR | image recognition, OCR, document extraction, field confidence, annotation, inspection | general AI, quality check without images/documents |
| Automation | RPA, bot, task automation, queue, exception handling, repetitive operation | productivity improvement without workflow detail |
| Conversational AI | chatbot, inquiry, conversation, escalation, answer candidate, support channel | FAQ as content only, general help page |
| Knowledge AI | internal search, RAG, documents, citations, source, knowledge base | FAQ, file management without AI retrieval |
| CRM | customer, opportunity, pipeline, sales activity, follow-up, CRM configuration | sales improvement without customer data |
| Generative AI | prompt, LLM, drafting, workbench, governance, internal AI use | AI keyword without output generation |
| Digital Experience | website, UX, CMS, site structure, EC, conversion, analytics | internal portal if knowledge search is dominant |
| Generic | no clear technical pattern, mixed consulting, early discovery | any strong signal above |

## 4. Compound Projects

| Compound case | Primary | Secondary | Rule |
|---|---|---|---|
| AI-OCR + RPA | Vision / OCR | Automation | Extraction defines the core value; automation defines downstream operation. |
| CRM + Generative AI | CRM | Generative AI | Customer data and sales workflow remain the main frame. |
| Web + AI chatbot | Digital Experience | Conversational AI | Website experience is primary; chatbot is a channel feature. |
| Knowledge Search + Generative AI | Knowledge AI | Generative AI | Retrieval and source grounding are primary. |
| RPA + CRM | Automation or CRM | CRM or Automation | Choose by whether operation automation or sales-data workflow is dominant. |

## 5. Confidence Rules

| Confidence | Action |
|---|---|
| 0.80 or higher | Use primary pack and include secondary pack modules if needed. |
| 0.60-0.79 | Use primary pack, but show category review warning in generation QA. |
| 0.40-0.59 | Use Generic Consulting Pack or ask for human category confirmation. |
| Under 0.40 | Use Generic Consulting Pack only. Do not inject category-specific terms. |

## 6. Fallback

Generic Consulting Pack is the safe fallback. It must not display unconditional AI, OCR, RPA, CRM, chatbot, web, CMS, or image-recognition terms.

## 7. Human Override

A future UI may allow admin or manager review to override:

- primary pack
- secondary pack
- roadmap type
- KPI pack
- estimate pack

Override should be recorded in audit logs when implemented in production. This Version 39.3 artifact does not implement that behavior.
