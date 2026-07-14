# AppShell UI Decomposition

Version 22.2では、UI仕様を変えずに `AppShell.tsx` の表示責務を分割した。

## 分割方針

- 表示文言、DOM順序、`id`、`data-testid`、`details/summary` 構造を維持する。
- 新しい画面、API、DB、権限、営業機能は追加しない。
- 分割先コンポーネントは props を受け取る表示中心の部品にする。
- AppShell側に状態管理と主要イベントを残し、子コンポーネントには副作用を増やさない。

## 追加したSection

| Component | 責務 |
| --- | --- |
| `AdminSection` | 管理者メニューのカテゴリ表示 |
| `WorkModeSection` | 他のAI機能・業務モード切替 |
| `DigitalCoworkerSection` | 会社調査・AI社員・MCP予定表示 |
| `SalesInfoSection` | 使い方・効果の説明表示 |
| `ProposalResultSection` | 提案結果、ダウンロード、品質、レビュー、最適化表示 |

## 維持した互換性

- `admin-menu-panel`
- `ai-functions-panel`
- `company-research-panel`
- `result-sales-panel`
- Beautiful.ai button `data-testid`
- UAT / jump button のスクロール先
- 既存CSS class
- 既存文言

## 行数目標

| ファイル | 変更前 | 変更後 |
| --- | ---: | ---: |
| `AppShell.tsx` | 5101 | 4475 |

最大の新規Sectionは `ProposalResultSection.tsx` で800行未満に収めた。
