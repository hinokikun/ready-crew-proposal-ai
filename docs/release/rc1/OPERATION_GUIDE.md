# RC1 Operation Guide

ProposalPilot Strategy v1 RC1の運用担当向け手順。

## 1. 現在のEngine Mode確認

Renderまたは実行環境の環境変数を確認する。

```text
PRESENTATION_ENGINE_MODE
```

値が未設定または `legacy` の場合、既存のLegacy Engineが使われる。

## 2. strategy_v1を有効化する

限定運用時のみ、環境変数を以下に設定する。

```text
PRESENTATION_ENGINE_MODE=strategy_v1
```

設定後、デプロイまたは再起動が必要な環境では反映操作を行う。

## 3. legacyへ戻す

不具合時または検証終了後は以下へ戻す。

```text
PRESENTATION_ENGINE_MODE=legacy
```

未設定でも既定値は `legacy` だが、運用上は明示的に `legacy` とする。

## 4. Strategy Brief Review

営業担当は以下を確認する。

- 案件カテゴリ
- Persona
- Decision Maker
- Strategy
- Story
- Presentation Pack
- KPI Pack
- Estimate Pack
- Main Message
- Priority Message
- Risk Message
- Next Action
- Confidence
- Evidence

承認結果は以下のいずれかとする。

- Approve
- Approve with Changes
- Reject
- Re-evaluate

`Approve` または `Approve with Changes` のみ次工程へ進める。

## 5. Quality Evaluator実行

例:

```powershell
python -m app.strategy_engine.cli --evaluate ai_ocr
python -m app.strategy_engine.cli --evaluate ai_ocr --format json
```

確認する項目:

- Total Score
- Grade
- Red Flags
- Category Scores
- Improvement Suggestions

## 6. Benchmark実行

全カテゴリ:

```powershell
python -m app.strategy_engine.cli --benchmark
```

カテゴリ指定:

```powershell
python -m app.strategy_engine.cli --benchmark --category vision_ocr
```

CSV:

```powershell
python -m app.strategy_engine.cli --benchmark --format csv
```

## 7. Compare実行

例:

```powershell
python -m app.strategy_engine.cli --compare ai_ocr
python -m app.strategy_engine.cli --compare crm --format json
```

確認する項目:

- Score差分
- Grade差分
- Persona差分
- Story差分
- Pack差分
- Red Flag差分
- Human Review差分
- 営業担当のHuman Evaluation欄

## 8. トラブル時の対応

| 事象 | 対応 |
|---|---|
| Strategy Briefが不自然 | Human ReviewでRejectまたはRe-evaluate |
| Red Flagが多い | Pilot対象から除外し、原因を記録 |
| PPT生成が失敗 | `legacy`へ戻して既存生成を確認 |
| Review Report不足 | Presentation Context生成へ進めない |
| Scoreが低い | CompareでLegacyとの差分を確認 |

## 9. 運用ログ

記録する項目:

- 実行日時
- Engine Mode
- 対象案件
- Reviewer
- Review結果
- Quality Score
- Grade
- Red Flag
- Compare結果
- 判断内容
