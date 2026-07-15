# Accessibility

## Required

- すべてのボタンに意味が分かるラベルを付ける
- input / textarea / checkbox は label と関連付ける
- キーボード操作で主要フローを完了できる
- `:focus-visible` を必ず表示する
- disabled の理由を画面上に表示する
- 色だけで状態を伝えない
- エラーと成功は日本語で表示する
- `aria-live` は処理状況、警告、エラーに使う
- モーダルはEscapeで閉じられる設計にする
- `prefers-reduced-motion` に対応する

## Quality Gate

一般画面では「提出前チェック」と表示します。

- チェック項目はキーボード操作可能にする
- 完了ボタンは常に見つけられる位置に置く
- 未確認項目数を表示する
- 完了後は完了日時、確認者、ステータスを表示する
