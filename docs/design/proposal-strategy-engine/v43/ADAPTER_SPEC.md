# Strategy Brief Adapter Specification

Status: implemented as offline bridge utility.

## Responsibility

The Strategy Brief Adapter performs one action:

```text
Approved HumanReviewReport
-> PresentationContext
```

It does not:

- call Presentation Engine
- generate PPTX
- call API
- save DB records
- run Strategy Engine again
- modify Strategy Brief evidence

## Input

The adapter accepts a `HumanReviewReport`.

The report must have one of these statuses:

- `approved`
- `approved_with_changes`

## Rejected Input

The adapter rejects:

- `rejected`
- `re_evaluate_required`

by raising an error.

## One-Way Conversion

Conversion is one-way.

```text
Strategy Brief -> Review Report -> Presentation Context
```

There is no reverse adapter from Presentation Context back to Strategy Brief.

## Design Reason

Presentation Engine should not interpret Strategy Brief directly. It should receive a focused rendering contract that contains only presentation-ready context.
