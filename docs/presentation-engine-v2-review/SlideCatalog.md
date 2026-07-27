# Slide Catalog

This catalog constrains Slide Intent AI and Story Engine outputs for sales, consulting, and executive proposal decks.

Minimum required catalog size: 80. This document defines 90 slide types.

---

## 1. Catalog Rules

- Each slide type has one primary communication purpose.
- Slide Intent AI selects slide type and goal only.
- Message Designer AI writes the headline and main message after slide type selection.
- Visual Director AI chooses visual expression after the slide type is known.
- Renderer never selects slide type.

---

## 2. Sales Proposal Slide Types

| ID | Slide type | Primary purpose | Common visual |
|---|---|---|---|
| S001 | Cover | establish proposal identity | hero visual |
| S002 | Title Divider | mark a chapter break | chapter band |
| S003 | Agenda | show discussion order | numbered list |
| S004 | Executive Summary | summarize decision point | three-point summary |
| S005 | One-page Proposal | compress full case | business case panel |
| S006 | Key Message | state one important point | large statement |
| S007 | Customer Context | show customer situation | context cards |
| S008 | Business Background | explain business backdrop | timeline or context map |
| S009 | Market Context | show external environment | market map |
| S010 | Industry Trend | describe industry trend | trend cards |
| S011 | Customer Challenge | define customer issue | problem map |
| S012 | Problem Statement | frame the main problem | issue cluster |
| S013 | Current State | explain current workflow | process flow |
| S014 | Current Pain Points | map pain by step | annotated flow |
| S015 | Root Cause | explain why issue happens | cause tree |
| S016 | Impact of Inaction | show cost of no action | risk/impact panel |
| S017 | Opportunity | define upside | opportunity cards |
| S018 | Target Outcome | describe desired state | outcome cards |
| S019 | Success Definition | define what good means | scorecard |
| S020 | Decision Criteria | clarify evaluation factors | criteria matrix |
| S021 | Stakeholder Map | show people involved | stakeholder map |
| S022 | Decision Maker View | adapt to decision maker | executive lens cards |
| S023 | User Persona | describe end users | persona card |
| S024 | Buyer Persona | describe buyer priorities | priority cards |
| S025 | Competitive Landscape | show competitors | quadrant or table |
| S026 | Competitor Comparison | compare alternatives | comparison table |
| S027 | Differentiation | state why us | differentiation matrix |
| S028 | Positioning | show proposal position | positioning map |
| S029 | Strategic Options | compare paths | option matrix |
| S030 | Recommended Strategy | recommend one approach | message pyramid |
| S031 | Proposal Overview | introduce solution | architecture overview |
| S032 | Solution Concept | explain core idea | concept diagram |
| S033 | Solution Architecture | show systems | layered architecture |
| S034 | Data Flow | explain data movement | data flow map |
| S035 | AI Workflow | show AI-human process | AI pipeline |
| S036 | Human Review Design | show review role | human-in-loop loop |
| S037 | Feature Overview | list features | icon card grid |
| S038 | Feature Detail | explain feature | annotated card |
| S039 | Use Case | show usage scenario | journey or flow |
| S040 | Business Process | show operational process | swimlane |
| S041 | Before After | show transformation | paired flow |
| S042 | Workload Reduction | explain efficiency | KPI cards |
| S043 | Quality Improvement | explain quality change | scorecard |
| S044 | Risk Reduction | show risk controls | risk control map |
| S045 | Compliance | explain governance | checklist |
| S046 | Security | explain security measures | layered defense |
| S047 | Operations Model | show operating model | operating model map |
| S048 | Support Model | show support structure | responsibility matrix |
| S049 | Team Structure | show team and roles | org chart |
| S050 | Delivery Approach | explain delivery method | stage gate |
| S051 | Project Scope | define included/excluded | scope table |
| S052 | Out of Scope | avoid misunderstanding | exclusion list |
| S053 | Implementation Plan | show execution plan | roadmap |
| S054 | Timeline | show schedule | timeline |
| S055 | Roadmap | show multi-phase future | roadmap lanes |
| S056 | Milestones | show decision points | milestone gate |
| S057 | PoC Plan | define pilot | stage gate |
| S058 | PoC Evaluation | define pilot metrics | evaluation matrix |
| S059 | KPI Definition | define metrics | KPI dashboard |
| S060 | Measurement Plan | show measurement method | scorecard |
| S061 | ROI Estimate | explain value | ROI bridge |
| S062 | Cost Benefit | compare cost and benefit | waterfall |
| S063 | Investment Summary | summarize spending | cost breakdown |
| S064 | Estimate Overview | explain estimate | estimate cards |
| S065 | Pricing Plan | show pricing options | pricing ladder |
| S066 | Assumptions | disclose assumptions | assumption map |
| S067 | Dependencies | show prerequisites | dependency map |
| S068 | Risk Register | list risks | risk matrix |
| S069 | Mitigation Plan | show mitigations | risk-control map |
| S070 | Issue Handling | show escalation | process flow |
| S071 | Case Study | prove capability | case card |
| S072 | Track Record | show experience | evidence stack |
| S073 | Reference Architecture | show proven pattern | architecture map |
| S074 | Demo Scenario | explain demo | storyboard |
| S075 | Screen Mock | show UX image | image placeholder |
| S076 | Data Requirements | define required data | checklist |
| S077 | Integration Requirements | define interfaces | integration map |
| S078 | Governance | define decision control | governance model |
| S079 | Change Management | explain adoption | maturity model |
| S080 | Training Plan | explain enablement | timeline |
| S081 | Communication Plan | show stakeholder communication | swimlane |
| S082 | FAQ | answer objections | FAQ cards |
| S083 | Objection Handling | address concerns | objection-response matrix |
| S084 | Next Actions | define next steps | action board |
| S085 | Approval Request | ask for decision | decision card |
| S086 | Closing | close proposal | closing message |
| S087 | Appendix Divider | separate appendix | divider |
| S088 | Detail Appendix | hold technical detail | structured text |
| S089 | Glossary | define terms | term table |
| S090 | Contact | show contact route | contact panel |

---

## 3. Required Slide Type Fields

Every slide type definition must be convertible to:

```json
{
  "slide_type_id": "S041",
  "slide_type": "before_after",
  "primary_goal": "show transformation",
  "default_visual_types": ["before_after_flow", "comparison_table"],
  "required_evidence": ["current_state", "proposed_state"],
  "optional_evidence": ["time_change", "risk_change"],
  "not_allowed": ["unverified_roi_numbers"],
  "review_questions": [
    "Can the audience understand before and after in 10 seconds?",
    "Are assumptions clearly labeled?"
  ]
}
```

---

## 4. Proposal Deck Coverage

Recommended minimum proposal deck:

1. Cover
2. Executive Summary
3. Customer Challenge
4. Current State
5. Before After
6. Proposal Overview
7. Solution Architecture or Business Process
8. KPI Definition
9. Implementation Plan
10. Estimate Overview
11. Risk Register
12. Next Actions

Short decks may use 6 to 8 slides. Executive decks may use 8 to 12 slides. Technical appendix slides should be separated from the main narrative.
