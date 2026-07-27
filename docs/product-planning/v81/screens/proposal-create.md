# SCR-020 Proposal Create

## Purpose

案件概要を最短で入力し、Prompt Builderまたはクイック入力へ進む。

## Layout

```text
[Page title: 新規提案]
[Mode tabs: クイック入力 | ステップ編集]
[Quick textarea] [Sample / How to]
[Start buttons: AIで提案書を作る | Stepで整理する]
```

## Validation

- 案件情報が空の場合は生成不可。
- 実在機密情報をテスト入力へ使わない注意を表示。
- Enterだけで生成しない。

## Current Implementation

Version80では`ProposalExperienceStudio`と既存`GuidedFlow`が併存。保存は主にUI stateと既存履歴。

