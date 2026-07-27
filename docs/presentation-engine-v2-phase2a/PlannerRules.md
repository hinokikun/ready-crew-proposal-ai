# Planner Rules

## Rule Families

- Story Arc Rules
- Audience Rules
- Decision Stage Rules
- Slide Count Rules
- Section Rules
- Transition Rules

## Story Arc Rules

- AI, automation, DX, CRM: `diagnosis_strategy_execution`
- Executive approval: `executive_decision`
- Competitive comparison: `insight_recommendation`
- Web, branding, hiring: `opportunity_solution_impact`
- Default: `problem_solution`

## Audience Rules

- CEO, executive, owner, CFO, CTO: executive
- Department head, director, manager: senior manager
- Field or operations leader: field leader
- IT or systems: information systems
- Unknown: general mixed audience

## Decision Stage Rules

- Approval or board signals: approval
- Budget present: comparison
- Renewal signals: renewal
- Otherwise: discovery

## Slide Count Rules

- Executive: 5 to 10 slides
- Standard: 8 to 14 slides
- Detailed: 12 to 25 slides

## Section Rules

Required baseline sections:

- Cover
- Problem or Current State
- Solution
- Next Action

Conditional sections:

- Executive Summary: executive or senior manager
- KPI: expected outcomes present
- ROI: budget and senior audience
- Pricing: budget present
- Competitor: competition present, except concise executive decks
- Appendix: detailed decks only

## Transition Rules

- Problem to solution uses `problem_to_solution`
- KPI or ROI to pricing uses `value_to_price`
- Risk to next action uses `risk_to_mitigation`
- Next action uses `summary_to_action`

