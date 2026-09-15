# Ready Crew Proposal AI — Canonical Visual Mapping

Status: `CANONICAL_VISUAL_MAPPING: LOCKED_FOR_DESIGN_REFERENCE`

## 1. Source of Truth

`docs/design/FINAL_VISUAL_MASTER.md` remains the sole formal Source of Truth for the Design Refresh.

This document records which approved screen-level Visual Master board is canonical for each existing Screen ID. It does not replace `FINAL_VISUAL_MASTER.md`, change application behavior, or authorize frontend implementation.

When this mapping conflicts with an older prototype or an unlisted visual proposal, the mapping below takes precedence for the relevant Screen ID, while the global principles in `FINAL_VISUAL_MASTER.md` remain authoritative.

## 2. Canonical Adoption Rules

- Use only the board version assigned to the Screen ID below.
- If the same Screen ID has multiple visual proposals, the explicitly assigned Canonical version is the priority reference.
- Do not mix components, layouts, robot treatments, scenery, or visual language from non-canonical alternatives into the assigned board.
- Mobile uses the `390px` version of each canonical board as the primary visual reference. Desktop and intermediate widths must preserve the same information hierarchy without treating mobile as a scaled desktop.
- The five approved Robots are the only Robot Visual Source: Green / Analysis, Flame-Orange / Strategy, Pink / Research, Red / Idea, and Brown-Tan / Final Check.
- Robots must use the approved visual source. Redrawing, CSS recreation, emoji substitution, recoloring, or replacement is prohibited.
- Pixel World elements are an environmental frame and brand layer. They must not obstruct business information, forms, tables, controls, primary actions, status messages, or accessible names.
- This mapping does not modify LEVEL 1 FROZEN CONTRACT: `data-testid`, `role`, `aria-*`, accessible names, panel IDs, navigation state, API conditions, permissions, Proposal step order, loading/disabled behavior, output/download behavior, modal behavior, Quality Gate behavior, and retry behavior remain unchanged.

## 3. Screen-to-Visual-Master Mapping

| Screen ID | Screen name / scope | Canonical Visual Master | Visual emphasis |
|---|---|---|---|
| HOME-01 | Authenticated Home | Batch 1 HOME-01 | Proposal starting point, stage orientation, restrained Pixel World, contextual Robot guide |
| LOGIN-01 | Login | Large brand-visual version | GAME START entrance, brand identity, clear authentication action and error visibility |
| SIGNUP-01 / ONBOARD-01 | Signup / Onboarding | 8-screen comprehensive board version | Guided entry, workspace/context setup, progressive information disclosure |
| USER-02 | Main user workspace | Later Batch 2 version | Operational workspace hierarchy and next action |
| AI-01 | AI assistant / analysis entry | Later Batch 2 version | AI role, current processing state, human confirmation |
| AI-02 | AI processing / result | Later Batch 2 version | Thinking state, evidence, confidence, next action |
| AI-03 | AI interaction / refinement | Later Batch 2 version | Human-in-the-loop refinement and controlled actions |
| AI-04 | AI completion / handoff | Later Batch 2 version | Completion state, review handoff, output readiness |
| CASE-01 | Case / project information | Batch 3 version | Structured case context and required information |
| CLIENT-01 | Client information | Batch 3 version | Client facts, relationship context, editable business fields |
| COMPETITION-01 | Competition / comparison | Batch 3 version | Comparative evidence and decision support |
| STRATEGY-01 | Proposal strategy | Batch 3 version | Strategy choices, rationale, and priority action |
| GENERATE-01 | Proposal generation | Batch 3 version | Generation readiness, progress, and controlled execution |
| PREVIEW-01 | Proposal preview | Other-pages board version | Readable review surface and output context |
| DOWNLOAD-01 | Download / delivery | Other-pages board version | Output format choices, completion feedback, download action |
| PROFILE-01 | Profile | Other-pages board version | Account information and low-risk settings |
| NOTIFICATION-01 | Notifications | Other-pages board version | Notification state, unread/attention hierarchy |
| PASSWORD-01 | Password/security | Other-pages board version | Security-sensitive form clarity and error handling |
| EDIT-01 | Detailed proposal edit | Case input → generation → edit → download → completion board version | End-to-end proposal workbench, editing focus, output continuity |
| ANALYSIS-02 | Analysis result | Analysis-results board version | Findings, evidence, confidence, unresolved items |
| DETAIL-01 | Detailed analysis / case detail | Analysis-results board version | Deep information hierarchy and supporting detail |
| ESTIMATE-01 | Estimate | Analysis-results board version | Numeric readability, assumptions, reviewability |
| HISTORY-01 | History | Batch 1 dashboard version | Resume/recent work, status, search and recency |
| ANALYTICS-01 | User analytics | Batch 1 dashboard version | Trend reading, useful summaries, action-oriented metrics |
| SETTINGS-01 | User settings | Batch 1 dashboard version | Grouped settings, safe defaults, low decoration |
| ADMIN-01 | Admin dashboard | Batch 1 dashboard version | Frequency, importance, risk, and operational state |
| HELP-01 | Help | Batch 5 version | Task-oriented help discovery |
| GUIDE-01 | Guide | Batch 5 version | Step-by-step assistance and contextual Robot guidance |
| FAQ-01 | FAQ | Batch 5 version | Scannable questions, categories, and answer hierarchy |
| CONTACT-01 | Contact | Batch 5 version | Clear support route and submission state |
| HELP-02 | Help secondary/detail | Batch 5 version | Related help, escalation, and return path |

## 4. Board Family Rules

### Batch 1

Canonical for `HOME-01`, `HISTORY-01`, `ANALYTICS-01`, `SETTINGS-01`, and `ADMIN-01` as specified above. Use the relevant board composition for each screen; do not copy Home-specific decoration into dense admin or analytics surfaces.

### Batch 2

Canonical for `USER-02`, `AI-01`, `AI-02`, `AI-03`, and `AI-04`. AI Robot feedback should communicate what the AI is doing, whether human confirmation is needed, and whether a result is finalized.

### Batch 3

Canonical for `CASE-01`, `CLIENT-01`, `COMPETITION-01`, `STRATEGY-01`, and `GENERATE-01`. Business content remains modern and readable; stage/progress accents support the proposal workflow without changing step order.

### Other pages

Canonical for `PREVIEW-01`, `DOWNLOAD-01`, `PROFILE-01`, `NOTIFICATION-01`, and `PASSWORD-01`. These screens use the shared Business UI Layer with only the amount of Adventure / Brand Layer appropriate to their task.

### End-to-end proposal board

Canonical for `EDIT-01`: the board spanning case input, generation, editing, download, and completion. This is a visual continuity reference only; it does not authorize changing the existing workflow or output behavior.

### Analysis-results board

Canonical for `ANALYSIS-02`, `DETAIL-01`, and `ESTIMATE-01`. Use a higher information density, explicit evidence/assumption treatment, and strong numeric readability.

### Batch 5

Canonical for `HELP-01`, `GUIDE-01`, `FAQ-01`, `CONTACT-01`, and `HELP-02`. These screens prioritize findability, readable support content, and clear return/escalation actions.

## 5. Mobile Canonical Rule

For every Screen ID, the `390px` board assigned to its canonical family is the primary mobile reference. Mobile reviews must verify:

- primary action remains reachable and visually clear;
- content becomes a single-column task sequence where appropriate;
- tables and dense information recompose without horizontal overflow;
- secondary navigation moves to the approved mobile shell pattern;
- Robot and Pixel World treatment is reduced or repositioned when it competes with the task;
- status, loading, error, disabled, and completion states remain understandable without color alone.

## 6. Implementation Boundary

This mapping is documentation only. It makes no changes to:

- frontend or backend source;
- CSS, TSX, TS, JS, assets, or prototypes;
- API calls, database behavior, feature flags, or permissions;
- navigation state or Proposal step order;
- Presentation Master, M30, renderer, Production, Render, or Vercel.

LEVEL 1 functional contracts remain frozen while each canonical board is translated into future visual-layer work.
