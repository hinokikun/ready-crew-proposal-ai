# Presentation Quality Score

## Model

総合100点。LLM判定だけではなく、決定論的ルールを組み合わせる。

| Category | Weight | Critical Example |
|---|---:|---|
| Story | 10 | Story不整合 |
| Customer Understanding | 8 | 顧客課題が不明 |
| Problem Definition | 8 | 課題が一般論 |
| Proposal Specificity | 8 | 提案内容が抽象的 |
| Evidence | 8 | 根拠なし断定 |
| Differentiation | 6 | 競合差別化なし |
| Executive Relevance | 6 | 決裁者向け価値なし |
| Sales Persuasiveness | 6 | Next Actionが弱い |
| Slide Objective | 6 | 1ページ1メッセージでない |
| Content Volume | 5 | 長文過多 |
| Readability | 5 | 小さすぎる文字 |
| Visual Hierarchy | 5 | 重要点が目立たない |
| Layout | 5 | 同じLayout連続 |
| Diagram Use | 4 | 文章だけ |
| Design Consistency | 4 | 色/余白が不一致 |
| Brand Consistency | 3 | Brand Kit未反映 |
| Estimate Consistency | 2 | 見積と本文不一致 |
| Next Action | 1 | 次の行動なし |

## Score Bands

- 90〜100: A, 顧客提出候補。
- 75〜89: B, 軽微修正後に提出候補。
- 60〜74: C, Storyまたは根拠の修正が必要。
- 0〜59: D, 再生成またはHuman Review必須。

## Red Flags

Evidence不足、ROI未説明、KPI欠落、Risk不足、Story不整合、見積不整合、顧客名不一致、Web制作固定文言の混入。

