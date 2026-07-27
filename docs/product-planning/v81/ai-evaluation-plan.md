# AI Evaluation Plan

## Objective

AI提案品質を外部APIに毎回依存せず継続評価する。

## Evaluation Inputs

- ProposalBrief fixture
- StrategyBrief
- StoryPlan
- SlidePlan
- QualityReport

## Metrics

- Story consistency
- Persona alignment
- Evidence coverage
- KPI quality
- Estimate consistency
- Web-fixed term leakage
- Red flag count
- Human Review required rate

## Process

1. fixtureを読み込む。
2. offline generatorまたは保存済みgoldenを使用。
3. quality evaluatorで採点。
4. Markdown/JSON/CSVでレポート。
5. LegacyとStrategy v1を比較。

