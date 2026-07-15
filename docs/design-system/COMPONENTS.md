# Components

Version 28.0では既存UIを一括置換せず、以下の共通部品を段階移行用に追加しました。

## Added Primitives

- `Button`
- `Card`
- `StatusBadge`
- `EmptyState`
- `Progress`
- `Spinner`

場所:

`frontend/components/ui/`

## Existing Class Compatibility

既存画面は引き続き以下のclassを利用できます。

- `primary-button`
- `secondary-button`
- `text-button`
- `field`
- `empty-state`
- `advanced-foldout`

Version 28.0ではこれらへProposalPilotトークンを反映し、既存動作を変えずに見た目を更新しました。

## Required States

すべての主要UIは以下を持つこと。

- hover
- focus-visible
- active
- disabled
- loading
- success
- warning
- error

## Button Rule

1画面・1ステップで最も重要な主ボタンは1つにすること。補助操作は `secondary-button` または `text-button` にすること。
