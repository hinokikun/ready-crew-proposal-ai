# Review Result Schema

Status: implemented as offline Pydantic models.

## HumanReviewResult

```json
{
  "decision": "approve_with_changes",
  "reviewer": "sales_user",
  "comment": "Persona and next action adjusted.",
  "reviewed_at": "2026-07-17T10:00:00+09:00",
  "overrides": [
    {
      "field": "primary_persona",
      "value": "department_head",
      "reason": "The meeting owner is the department head."
    }
  ]
}
```

## Decision Values

- `approve`
- `approve_with_changes`
- `reject`
- `re_evaluate`

## HumanReviewReport

The generated report includes:

- `schema_version`
- `decision`
- `reviewer`
- `comment`
- `reviewed_at`
- `status`
- `applied_overrides`
- `rejected_overrides`
- `review_required_before_presentation`
- `original_brief`
- `reviewed_brief`
- `markdown_summary`

## Status Mapping

| Decision | Status |
|---|---|
| approve | approved |
| approve_with_changes | approved_with_changes |
| reject | rejected |
| re_evaluate | re_evaluate_required |

## Boundary

The report can be serialized to JSON or Markdown. Version 42 does not save it to DB.
