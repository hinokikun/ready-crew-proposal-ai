# Generation Job Design

## Purpose

AI生成、PPTX、PDF、Beautiful.aiなどの長時間処理を安全に管理する。

## Job States

- queued
- running
- waiting_review
- succeeded
- failed
- cancelled
- retrying

## Job Fields

- job_id
- organization_id
- workspace_id
- project_id
- proposal_id
- version_id
- job_type
- status
- current_step
- progress_percent
- started_at
- finished_at
- request_id
- error_type
- safe_error_message

## Steps

Strategy, Story, Slide Planning, Designer, Quality, PPTX, PDF, Beautiful.ai, Save.

## Idempotency

同じProposalVersionとExportTargetで連打された場合、実行中Jobを返す。二重生成を避ける。

## Rollback

Job失敗時に既存ProposalVersionは保持する。Artifactは成功時だけ公開する。

