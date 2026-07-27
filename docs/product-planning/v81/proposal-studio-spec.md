# Proposal Studio Specification

## Positioning

Proposal StudioはAI営業秘書の中心画面である。汎用PowerPointエディターではなく、営業提案のStory、Slide、Design、Quality、Exportを管理する編集画面とする。

## Layout

```text
[Top bar]
  Proposal name | save status | undo | redo | preview | export
[Left]
  slide thumbnails | warning | add | duplicate | delete | move
[Center]
  16:9 slide preview | editable title/body | visual area | guides | zoom
[Right]
  AI | Design | Layout | Content | Quality | Comments | History
[Bottom]
  generation status | unresolved warnings | review comments
```

## Version 82 Scope

- SlidePlanベースのHTML近似プレビュー。
- スライドタイトル、Core Message、本文、Visual Intentの編集。
- Undo / Redoの最小単位は「SlidePlan field change」。
- Autosaveは5秒debounce、失敗時は画面上部に警告。
- PPTX生成は既存`/download-pptx`互換APIを呼ぶ。
- 既存Proposalは読み取り専用または互換変換で開く。

## Future Scope

- 要素単位のドラッグ編集。
- 共同編集、ロック、コメント解決。
- PPTX round-trip import。
- 詳細なVisual Regression。

## Data Format

Studio内部は`ProposalVersion`配下に`StoryPlan`、`SlidePlan[]`、`DesignTheme`、`QualityReport`を保存する。Version80時点ではDB未実装のため、Version82でmigrationを追加する。

## HTML Preview vs PPTX

HTMLプレビューは編集体験を優先し、PPTX出力は最終生成物とする。差異をゼロにするのではなく、以下を保証する。

- スライド数、タイトル、本文、図解意図は一致。
- テンプレート、主要色、余白、見出し階層は近似。
- 詳細なShape位置はPPTX生成時に最終調整。

## Error Handling

- Autosave失敗: 編集継続可能、手動保存を提示。
- PPTX生成失敗: Studio内容は保持し、Exportだけ再試行。
- 権限不足: 読み取り専用にする。
- 旧Proposal変換失敗: 旧結果表示へフォールバック。

## Completion Criteria

- memberが新規ProposalをStudioで編集できる。
- viewerは閲覧のみ。
- Workspace外Proposalを開けない。
- PPTX生成後も既存Proposalフローが壊れない。

