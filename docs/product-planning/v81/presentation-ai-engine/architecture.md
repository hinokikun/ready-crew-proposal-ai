# Presentation AI Engine Architecture

## Input

- ProposalBrief
- StrategyBrief
- StoryPlan
- SlidePlan
- DesignTheme
- BrandSettings

## Output

- RenderableSlidePlan
- PPTXGenerationContext
- QualityReport
- ExportArtifacts

## Boundary

Presentation AI EngineはStory判断を再実施しない。StoryPlanを受け取り、表示設計、レイアウト、図解、品質調整に責務を限定する。

## Deterministic vs AI

| 領域 | 決定論的 | AI |
|---|---|---|
| 文字数上限 | yes | no |
| 最低フォントサイズ | yes | no |
| Layout候補 | yes | yes |
| 図解意図 | no | yes |
| 色コントラスト | yes | no |
| Story適合性 | mixed | mixed |
| Evidence不足 | yes | yes |

## Failure Fallback

AI選択が失敗した場合は、Corporate Clean + safe layout + 文字量圧縮提案へフォールバックする。PPTX生成失敗時はProposal Studio内容を保持する。

