# Review Screen Specification

Status: future UI design only. No frontend implementation in Version 42.

## 1. Screen Purpose

The review screen should help a sales user understand the Strategy Brief without exposing unnecessary technical details.

## 2. Display Sections

1. Summary
2. Audience
3. Strategy
4. Story
5. Presentation Input
6. Evidence
7. Human Review Reasons
8. Editable Fields
9. Review Decision

## 3. Summary

Display:

- Category
- Persona
- Strategy
- Story
- Presentation Pack
- Confidence

## 4. Evidence

Display evidence as:

- Confirmed
- Provided
- Inferred
- Missing

Evidence should be read-only.

## 5. Editable Area

Editable fields should be grouped:

- Persona and audience
- Story direction
- Hero and message
- Priority messages
- Risk messages
- Next actions

## 6. Actions

Primary actions:

- Approve
- Approve with Changes
- Reject
- Re-evaluate

## 7. Error and Warning Rules

Warn when:

- confidence is low
- Generic fallback was selected
- persona is unknown
- prohibited terms were detected
- evidence is missing

## 8. Version 43 Boundary

This screen spec does not create or connect a frontend screen. It defines the future behavior only.
