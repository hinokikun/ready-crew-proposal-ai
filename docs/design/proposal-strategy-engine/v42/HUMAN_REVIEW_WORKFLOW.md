# Human Review Workflow

Status: specification only. Production flow connection is prohibited in Version 42.

## 1. Purpose

Strategy Brief should not be treated as final just because the Strategy Engine generated it.

Sales users must be able to:

- confirm
- correct
- approve
- reject
- request re-evaluation

before any presentation generation uses the Strategy Brief.

## 2. Workflow

```text
案件入力
-> Strategy Engine
-> Strategy Brief
-> Human Review
-> Review Result
-> Approved Strategy Brief
-> Presentation Engine
```

Version 42 stops at Review Result.

## 3. Review Targets

Sales users should review:

- 案件カテゴリ
- Persona
- Decision Maker
- Strategy
- Story
- Presentation Pack
- KPI Pack
- Estimate Pack
- Hero Theme
- Main Message
- Priority Message
- Risk Message
- Next Action
- Confidence
- Evidence
- Human Review理由

## 4. Review Decisions

| Decision | Meaning | Next step |
|---|---|---|
| Approve | Strategy Brief is accepted as-is. | Future Version 43 may pass it to Presentation Engine. |
| Approve with Changes | Editable fields were changed and accepted. | Future Version 43 may pass reviewed brief. |
| Reject | Strategy is not acceptable. | Human or Strategy Engine must restart from intake. |
| Re-evaluate | More information or different assumptions are needed. | Strategy Engine should run again with updated input. |

## 5. Gate Rule

Presentation Engine must not receive a Strategy Brief unless review status is:

- `approved`
- `approved_with_changes`

This gate is a design requirement for Version 43.

## 6. Audit Design for Future Version

When connected later, the system should record:

- reviewer
- reviewed_at
- decision
- applied overrides
- rejected overrides
- comment
- original brief
- reviewed brief
