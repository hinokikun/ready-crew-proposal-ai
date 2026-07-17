# Term Guard

Status: deterministic category term guard.

## Purpose

Term Guard prevents category-specific terms from leaking into unrelated proposals.

Example:

- OCR proposal should not inject CMS, SEO, site map, or conversion terms.
- Generic Consulting proposal should not inject OCR, RPA, CRM, chatbot, CMS, or SEO terms unless they are explicitly selected.

## Term Groups

The evaluator produces:

- `allowed_terms`
- `conditional_terms`
- `prohibited_terms`

Primary pack terms are allowed. Secondary pack terms are conditional. Other category-specific terms are prohibited.

## Ambiguous Terms

Common business terms are not treated as prohibited terms. The guard should focus on category-specific terms.

## Production Rule for Future Versions

Presentation generation should validate generated content against `prohibited_terms` before final output.
