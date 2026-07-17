# Extension Guide

将来ProposalPilotを拡張する場合の安全な進め方。

## 共通ルール

- 既定値はLegacy互換を維持する
- Feature Flagなしに本番挙動を変えない
- Human Reviewを通さずStrategy v1を本番生成に渡さない
- DB変更が必要な場合はMigrationとRollback計画を用意する
- 実顧客データや秘密情報をfixtureに入れない
- 新規ルールを追加したらEvaluation HarnessとComparison Frameworkで評価する

## 新しいPresentation Packを追加する場合

1. Packの目的と適用カテゴリを設計する
2. `PresentationPack` enumへ追加する
3. `rules.py` の選定ルールを追加する
4. Golden testを更新する
5. Quality EvaluatorでPack整合性を確認する
6. Benchmark Datasetへサンプルを追加する
7. Pilotで人間評価を行う

## 新しいStoryを追加する場合

1. Storyの対象Personaと意思決定ポイントを定義する
2. `StoryType` enumへ追加する
3. `rules.py` のStory選定を追加する
4. Required / Optional slide設計を追加する
5. Golden testを更新する
6. Compare ReportでLegacyとの差分を確認する

## 新しいPersonaを追加する場合

1. 重要視する内容、嫌う内容、意思決定ポイントを整理する
2. `Persona` enumへ追加する
3. Persona選定ルールを追加する
4. Story分岐への影響を確認する
5. Human Review項目に必要な補足を追加する

## 新しいQuality Ruleを追加する場合

1. 評価カテゴリまたはRed Flagの目的を定義する
2. `quality.py` に採点関数を追加する
3. Scoreの上限と減点理由を明確にする
4. `quality_fixtures.py` に不足ケースを追加する
5. `test_quality_evaluator.py` を追加・更新する
6. Benchmark / Compare出力で確認する

## 新しいEvaluation Datasetを追加する場合

1. 匿名化された案件概要を用意する
2. `fixtures.py` に安全なfixtureを追加する
3. `benchmark_dataset.py` にケースを追加する
4. カテゴリ別の件数バランスを確認する
5. `--benchmark --category` で出力を確認する

## 新しいCLI出力を追加する場合

1. 既存の `--fixture` `--review` `--evaluate` `--benchmark` `--compare` と競合しない形にする
2. Markdown / JSONの互換を壊さない
3. CSV追加時は列名を固定する
4. CLIテストを追加する

## 本番接続する場合の追加確認

- Feature Flag設計
- Legacy fallback
- Human Review必須条件
- Organization / Workspace分離
- Audit Log
- Rate Limit
- Error response
- Rollback Plan
- Full pytest
- Frontend E2E
