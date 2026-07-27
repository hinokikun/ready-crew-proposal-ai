# Phase 3 Implementation Guide

## Goal

Phase 3 should implement Visual Director. It should convert Slide Intent Output into a Visual Plan.

## Inputs

- Slide Intent Output
- selected Slide Intent Design
- information priority
- reading order
- visual pattern candidate
- diagram candidate
- chart candidate
- layout constraints
- warnings

## Outputs

Future Visual Plan should include:

- visual strategy
- selected diagram type
- selected chart type
- visual hierarchy
- composition type
- content grouping
- emphasis target
- image placeholder requirement
- accessibility note
- downstream blueprint requirements

## What Visual Director Decides

- whether the slide is best expressed as comparison, timeline, matrix, cards, process, KPI, roadmap, callout, image, or table
- how content should be grouped visually
- which items should be primary, secondary, or muted
- whether the slide should be split before rendering

## What Visual Director Must Not Decide

- headline
- main message
- business strategy
- evidence truth
- exact coordinates
- fonts
- final colors
- PowerPoint objects

## Required Tests

- visual selection by slide intent
- evidence gap handling
- numeric chart suppression when evidence is missing
- one-message preservation
- deterministic output
- fixture and golden coverage
- downstream boundary checks
