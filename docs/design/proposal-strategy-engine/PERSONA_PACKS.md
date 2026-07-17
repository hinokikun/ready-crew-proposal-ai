# Persona Packs

Version: 40.0
Status: Design only. No production implementation.

## 1. Purpose

Persona Pack defines how Proposal Strategy Engine should adapt the proposal to the reader.

The same project can require different stories:

- CEO wants investment meaning and strategic risk.
- Field lead wants operational fit and workload impact.
- IT wants integration, security, and maintainability.

## 2. Persona List

| Persona | Japanese label | Primary concern |
|---|---|---|
| CEO | CEO / 経営者 | business impact and decision risk |
| Executive | 役員 | investment, governance, cross-department value |
| Department Director | 部長 | department outcome and implementation feasibility |
| Manager | 課長 | team workload, schedule, measurable improvement |
| Field Lead | 現場責任者 | daily operation, burden, acceptance |
| Information Systems | 情報システム | integration, security, maintenance |
| Quality Assurance | 品質保証 | standards, traceability, defect prevention |
| Sales | 営業 | customer response, opportunity progress, sales quality |

## 3. CEO

| Item | Guidance |
|---|---|
| 重要視する内容 | strategic priority, investment meaning, competitive impact, governance, decision timing |
| 嫌う内容 | detailed feature lists before business meaning, ungrounded technical claims, vague ROI |
| 意思決定ポイント | why now, expected business change, risk if delayed, required investment, executive decision item |
| 説明順 | market or business issue -> strategic option -> investment value -> risk control -> decision request |

## 4. Executive

| Item | Guidance |
|---|---|
| 重要視する内容 | cross-functional effect, budget logic, risk mitigation, rollout control |
| 嫌う内容 | single-department optimization without enterprise effect, unclear owner, unsupported payback |
| 意思決定ポイント | investment range, governance model, KPI definition, organization impact |
| 説明順 | current issue -> expected outcome -> organization plan -> KPI -> approval point |

## 5. Department Director

| Item | Guidance |
|---|---|
| 重要視する内容 | department productivity, quality, implementation schedule, responsibility split |
| 嫌う内容 | executive-only abstraction, implementation burden hidden late, unrealistic roadmap |
| 意思決定ポイント | department benefit, schedule feasibility, affected teams, success conditions |
| 説明順 | department problem -> solution concept -> before/after -> PoC plan -> resource request |

## 6. Manager

| Item | Guidance |
|---|---|
| 重要視する内容 | team workload, concrete steps, deliverables, risk during transition |
| 嫌う内容 | large transformation language without action plan, unclear task owner |
| 意思決定ポイント | workload reduction, task change, schedule, training requirement |
| 説明順 | current operation -> task pain -> proposed process -> rollout tasks -> acceptance criteria |

## 7. Field Lead

| Item | Guidance |
|---|---|
| 重要視する内容 | daily usability, error prevention, exception handling, human review |
| 嫌う内容 | "full automation" claims that ignore field exceptions, black-box AI |
| 意思決定ポイント | whether work becomes easier, whether final human judgment remains, whether mistakes are recoverable |
| 説明順 | current workflow -> pain point -> assisted workflow -> screen or operation image -> PoC |

## 8. Information Systems

| Item | Guidance |
|---|---|
| 重要視する内容 | architecture, data flow, API, security, permission, maintenance |
| 嫌う内容 | vague integration wording, missing data ownership, no failure mode |
| 意思決定ポイント | integration method, security boundary, operation model, support responsibility |
| 説明順 | current system constraint -> architecture -> integration -> security -> operation plan |

## 9. Quality Assurance

| Item | Guidance |
|---|---|
| 重要視する内容 | accuracy, traceability, approval, auditability, standardization |
| 嫌う内容 | "AI will decide" without evidence, no history, no correction process |
| 意思決定ポイント | standard definition, review history, defect reduction, audit evidence |
| 説明順 | quality variance -> review process -> evidence and log -> KPI -> control plan |

## 10. Sales

| Item | Guidance |
|---|---|
| 重要視する内容 | customer response speed, proposal quality, follow-up, CRM consistency |
| 嫌う内容 | internal-only efficiency framing, complex admin settings, weak customer value |
| 意思決定ポイント | faster proposal cycle, better customer fit, fewer missed actions, sales pipeline visibility |
| 説明順 | customer issue -> sales action -> AI assistance -> proposal output -> CRM / follow-up |

## 11. Persona Selection Rules

| Signal | Recommended persona |
|---|---|
| budget approval, board, investment, management | CEO or Executive |
| department, division, productivity, quality | Department Director |
| team operation, daily tasks, workload | Manager or Field Lead |
| integration, API, DB, security, SSO | Information Systems |
| inspection, compliance, defects, audit | Quality Assurance |
| customer, opportunity, proposal, follow-up | Sales |

## 12. Mixed Persona Handling

If multiple personas are likely, Strategy Engine should produce:

- Primary Audience: the person who must say yes.
- Secondary Audience: the people who can block adoption.
- Slide emphasis: early pages for Primary Audience, middle pages for Secondary Audience.

Example:

```json
{
  "primary_audience": "department_director",
  "secondary_audience": ["information_systems", "field_lead"],
  "story_adjustment": "business outcome first, architecture and operation second"
}
```
