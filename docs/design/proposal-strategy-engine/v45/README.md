# Version 45 Proposal Quality Evaluation Framework

Status: offline quality evaluation only. Production generation is unchanged.

Version 45 adds a Proposal Quality Evaluator that scores the outputs of the Strategy workflow before presentation generation.

## Input

- Strategy Brief
- Human Review Report
- Presentation Context

## Output

- Proposal Quality Report JSON
- Proposal Quality Report Markdown

## Boundary

Version 45 does not change:

- PPTX generation logic
- Presentation Engine runtime behavior
- Strategy decision rules
- frontend
- database
- migrations
- external AI services
- presentation integrations

## CLI

```text
python -m app.strategy_engine.cli --evaluate ai_ocr
python -m app.strategy_engine.cli --evaluate ai_ocr --format json
```

## Purpose

The evaluator answers:

- Is the proposal story coherent?
- Is it aligned to the target persona?
- Is the selected strategy reflected in the Presentation Context?
- Are KPI, evidence, risks, roadmap, and next actions sufficient?
- Are there red flags that should stop progression to presentation generation?
