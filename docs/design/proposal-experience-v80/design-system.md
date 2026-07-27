# Design System

## カラー

- Navy: 信頼感と背景
- Blue: 主操作、選択状態
- Cyan: AI補助、強調
- Green: 成功
- Orange: 注意
- Red: エラー
- White / Light Surface: 業務画面の読みやすさ

## UI

- カードは情報のまとまりに限定する
- 角丸は中程度にし、業務アプリとして過度に装飾しない
- 影は軽く、現在地と重要操作の強調に使う
- 入力欄、ボタン、タブは42px以上を基本とする
- focus-visibleを明示する

## アニメーション

短いサイドバー開閉など、状態変化の理解に必要な範囲へ限定します。`prefers-reduced-motion`では遷移を止めます。

