# SCR-030 Prompt Builder

## Purpose

案件基本情報、顧客、課題、条件、方針を段階的に入力する。

## Layout

```text
[Step rail] [Form section] [Smart prompts / quality hints]
```

## Fields

- 案件名、クライアント名、業種、案件種別、期限。
- 顧客事業、対象ユーザー、意思決定者、重視点。
- 現状、顕在課題、潜在課題、背景、リスク。
- 予算、納期、スコープ、必要機能、制約、競合。
- 訴求、トーン、資料長、デザイン、出力形式。

## Autosave

Version82ではProposalBrief draftとして保存。現在はUI state中心のため、画面更新で失われる可能性がある。

## Accessibility

すべての入力にlabelを付け、現在Stepをaria-currentで示す。

