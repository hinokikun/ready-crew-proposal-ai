# Migration Guide

## 方針

既存UIを一括置換しない。以下の順で安全に移行する。

1. Design Tokenを使う
2. 既存classをProposalPilotトーンへ揃える
3. 新規画面から `frontend/components/ui/` の共通部品を使う
4. 既存画面は改修時に段階移行する
5. API、DB、権限、生成処理はUI移行と同時に変更しない

## 置換の目安

- 重要な主操作: `Button variant="primary"`
- 補助操作: `Button variant="secondary"`
- 危険操作: `Button variant="danger"`
- 空状態: `EmptyState`
- 状態表示: `StatusBadge`
- 読み込み: `Spinner` または Skeleton

## 禁止

- 管理者診断を一般利用者画面へ表示する
- 1ステップに同じ強さの主ボタンを複数置く
- disabled 理由を非表示にする
- 技術用語だけでエラーを表示する
