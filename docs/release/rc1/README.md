# ProposalPilot Strategy v1 RC1

Version48では、ProposalPilot Strategy v1をRelease Candidate 1として運用確認できる状態に整理する。

このRC1は新しい提案生成機能ではない。Version47までに作成したStrategy Engine、Presentation Context、Human Review、Quality Evaluator、Evaluation Harness、Comparison Frameworkを、安全に運用評価するための準備資料である。

## RC1の目的

- `strategy_v1` を限定運用できるか確認する
- 既定値 `legacy` を維持し、既存利用者への影響を避ける
- Human Reviewを通過したStrategy Briefのみ利用する
- Quality ScoreとRed Flagを見ながら段階的に評価する
- 不具合時はFeature Flagで即座にLegacyへ戻せるようにする

## 対象範囲

- Feature Flag確認
- Legacyフォールバック確認
- Human Review運用
- Quality Evaluator運用
- Benchmark運用
- Compare運用
- RC1受入条件
- パイロット計画
- ロールバック計画

## 対象外

- 新しいStrategy追加
- 新しいPresentation Pack追加
- 新しいAI機能追加
- DBスキーマ変更
- Migration追加
- OpenAI利用方法変更
- Beautiful.ai仕様変更
- Frontend大幅変更

## 関連資料

- `docs/design/proposal-strategy-engine/v44/FEATURE_FLAG.md`
- `docs/design/proposal-strategy-engine/v45/README.md`
- `docs/design/proposal-strategy-engine/v46/README.md`
- `docs/design/proposal-strategy-engine/v47/README.md`
