# Prompt Builder Specification

## Purpose

非構造の案件情報を、AIが安全に扱えるProposalBriefへ変換する。入力を増やすことではなく、提案品質に効く不足情報を少数ずつ確認する。

## Sections

| Section | Fields | Required |
|---|---|---|
| 案件基本情報 | 案件名、顧客名、業種、案件種別、提案期限 | 案件名、顧客名、案件種別 |
| 顧客情報 | 事業内容、対象ユーザー、意思決定者、関係者、重視点 | 条件付き |
| 背景 / 現状 | 現状、背景、既存運用 | 任意 |
| 課題 | 顕在課題、潜在課題、リスク | 1件以上 |
| 提案条件 | 予算、納期、スコープ、必要機能、制約、競合 | 条件付き |
| 期待成果 | KPI、成功条件、品質条件 | 任意 |
| 提案方針 | トーン、資料長、デザイン、出力形式 | 任意 |

## Input Modes

- Step mode: 標準。
- Quick input: 既存の自由入力互換。
- File input: Version83以降。
- Past proposal copy: Version83以降。
- AI questions: Version82。
- AI assumptions: 承認されるまで確定値にしない。
- Template: Version82。

## Validation

- 文字数上限をsection別に設定する。
- 案件名、顧客名、課題が空なら生成不可。
- 予算、納期は不明を許容するが、不明として管理する。
- AI推定は`assumption`として保存し、confirmedとは分ける。

## Smart Questions

優先度は以下で決める。

1. 提案成立に必須: 顧客名、課題、目的、納期。
2. 説得力に効く: 予算、KPI、意思決定者、競合。
3. デザイン/出力に効く: 資料長、トーン、テンプレート。

一度に表示する質問は最大3件。

## Autosave

Version82で`ProposalBrief.status=draft`へ保存する。保存失敗時は編集を止めず、未保存状態を明示する。

## Generation Start Conditions

- Roleがmember以上。
- Workspace contextが存在。
- 入力品質スコアが最低条件を満たす、またはユーザーが不足を承知して続行。
- maintenance modeでは生成不可。

