# Quality Report Schema

## JSON Shape

```json
{
  "schema_version": "proposal_quality_report_v1",
  "total_score": 88,
  "grade": "A",
  "category_scores": [
    {
      "category": "Story Consistency",
      "score": 10,
      "reason": "story, required slides, and context are aligned",
      "suggestion": "Align story type and required slide order before presentation generation."
    }
  ],
  "red_flags": [
    {
      "code": "kpi_missing",
      "severity": "high",
      "category": "KPI Quality",
      "message": "KPI pack or KPI slide coverage is missing."
    }
  ],
  "summary": "Proposal quality is strong and ready for human final review.",
  "reviewed_strategy_schema_version": "strategy_brief_v1",
  "presentation_context_version": "presentation_context_v1",
  "review_status": "approved"
}
```

## Markdown Shape

```text
# Proposal Quality Report

- Total Score: 88 / 100
- Grade: A

## Category Scores
### Story Consistency
- Score: 10 / 10
- Reason: ...
- Improvement: ...

## Red Flags
- None
```

## Excluded Data

The report must not include:

- full customer input
- passwords
- API keys
- tokens
- external service secrets
- full proposal body
