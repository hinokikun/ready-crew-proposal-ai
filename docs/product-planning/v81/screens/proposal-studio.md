# SCR-080 Proposal Studio

## Purpose

AI営業秘書の中心画面。スライド構成、内容、デザイン、品質を1か所で調整する。

## Layout

```text
[Top: file name | saved | undo | redo | preview | export]
[Left pane: slide thumbnails]
[Center pane: slide canvas]
[Right pane tabs: AI | Design | Layout | Content | Quality | Comments | History]
[Bottom: warnings / generation status]
```

## Operations

- スライド選択、追加、複製、削除、上下移動。
- タイトル、本文、図解意図の編集。
- AI改善案の比較、適用、却下。
- Quality findingの確認。

## Responsive

PCは3ペイン。900px未満は左/中央/右をタブ化。

## Version82 Scope

HTML近似プレビュー、SlidePlan編集、Undo/Redo、Autosave、PPTX生成への連携を優先する。PowerPoint完全互換エディターは目指さない。

