# SCR-010 Dashboard

## Purpose

営業担当者が今日必要な提案状況だけを確認し、2クリック以内で新規提案へ進む。

## Layout

```text
[Top Bar: workspace / search / notifications]
[Sidebar]
  [Hero action: 新しい提案を作成]
  [Today cards: 提案待ち / 期限近い / 優先案件]
  [Recent proposals] [AI recommendations]
  [Weekly metrics: 提案数 / 平均作成時間 / 累計削減]
```

## Components

- ProposalAgentDashboard
- GuidedFlow summary
- Creation history summary
- Beautiful.ai status chip

## States

- Loading: KPI skeleton.
- Empty: 「案件はまだありません」＋「新しい提案を作成」。
- Error: Backend接続、認証切れ、権限不足を分ける。

## Responsive

PCは2〜3カラム。タブレットは2カラム。スマートフォンは1カラムでCTAを上部固定。

## Accessibility

カード見出しをh2/h3で整理し、主要CTAへキーボードで到達できること。

