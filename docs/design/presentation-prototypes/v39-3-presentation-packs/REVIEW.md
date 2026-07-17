# ProposalPilot V39.3 Presentation Packs Review

Status: design approval prototype only. Not integrated into production PPTX generation.

## 1. Prototype Summary

This package contains 8 category presentation packs. Each pack has 4 representative pages:

1. Hero
2. Current / Future
3. Architecture
4. KPI

Total: 32 slides.

## 2. Pack Review

| Pack | Main visual lead | Applies to | Does not apply to | V39.1 difference | 3-second view | 10-second understanding | Sales explanation | Production risk |
|---|---|---|---|---|---|---|---|---|
| Vision / OCR | Recognition/extraction work frame | image recognition, AI-OCR | Web, CRM-only | Keeps V39.1 closest | scan/work frame | AI reads, human confirms | extraction quality is measured in PoC | low |
| Automation | task queue and bot execution | RPA, automation | OCR-only, web-only | changes recognition to orchestration | automation lane | bots handle standard work, humans review exceptions | automate work without losing control | medium |
| Conversational AI | conversation and escalation flow | chatbot, inquiry response | OCR, web-only | changes frame to conversation UI | chat flow | AI answers routine questions, humans handle exceptions | reduce response load safely | medium |
| Knowledge AI | grounded search and source cards | RAG, internal search | CRM-only, web-only | changes frame to retrieval | source cards | answer quality depends on sources and permission | search with evidence, not generic answers | medium |
| CRM | customer 360 and action candidate | CRM, sales intelligence | OCR, web-only | changes frame to customer/action workspace | customer workspace | sales action candidates support human judgment | improve data quality and follow-up | medium-high |
| Generative AI | AI workbench and review | GenAI adoption | OCR-only, web-only | changes frame to output review and governance | workbench | generated outputs require review and rules | productivity with governance | medium-high |
| Digital Experience | journey, site, CMS, measurement | Web, UX, EC | OCR, RPA-only | avoids recognition frame entirely | device/journey | web value comes from experience and measurement | redesign experience and operations | high |
| Generic | decision map and execution path | unclear or mixed projects | clear category projects | removes specific terms | decision map | organize facts before selecting solution | safe fallback when category confidence is low | medium |

## 3. Human Review Points

For every pack, human reviewers should confirm:

- The pack's hero visual fits the intended category.
- The architecture page is not just a box-name swap.
- KPI names are category-appropriate.
- Estimate items do not feel generic or wrong.
- No terms from other packs leak into the slides.
- The ProposalPilot brand remains recognizable.

## 4. Production Integration Risks

Critical risks before Version40:

1. Incorrect pack selection could produce misleading decks.
2. Category terms could leak into unrelated proposals.
3. Estimate items could look fake if not category-bound.
4. Architecture pages could become generic if data flow semantics are not encoded.
5. Digital Experience requires a distinct visual language and must not be forced into AI recognition style.

## 5. Human Approval Gate

Do not integrate these packs into the production PPTX generation engine until humans approve:

- pack selection logic
- category terminology
- architecture variants
- KPI packs
- estimate packs
- visual consistency across all 8 packs
