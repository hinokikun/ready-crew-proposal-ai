# Scoring

## Category Score

Each category is scored from 0 to 10.

| Score | Meaning |
|---|---|
| 9-10 | Strong. Ready for final human review. |
| 7-8 | Usable. Minor review recommended. |
| 5-6 | Weak. Improve before presentation generation. |
| 0-4 | Serious gap. Human review required. |

## Total Score

The total score is the sum of ten category scores.

```text
total_score = sum(category_scores)
```

Maximum score is 100.

## Grade

| Grade | Range |
|---|---|
| A | 85-100 |
| B | 70-84 |
| C | 55-69 |
| D | 0-54 |

## Rule

High total score does not override red flags.

If a critical red flag exists, the report should not proceed to presentation generation until reviewed.
