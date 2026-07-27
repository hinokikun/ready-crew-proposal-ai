# Version81 Demo Script

Ready Crew Proposal AI / ProposalPilot
Version81 Training Demo

作成日: 2026-07-26

---

## 1. デモの目的

Version81のデモでは、単にPowerPointを生成する場面ではなく、次の流れを見せます。

1. 案件情報を入力する。
2. Sales Strategy AIが営業戦略を整理する。
3. 営業担当者がProposal Strategy Workspaceで確認、編集、採用する。
4. Story Engineへ確定Strategyを渡す。
5. Presentation Designer AIがスライドごとのLayoutを提案する。
6. Presentation Quality Engineが資料品質を評価する。
7. 必要に応じてAuto Fixを適用し、PPTX生成へ進む。

---

## 2. 5分デモ構成

| 時間 | 操作 | 説明 |
|---|---|---|
| 0:00〜0:30 | ログインし、Proposal Studioを開く | Version81では提案作成の前に営業戦略と資料品質を確認できる |
| 0:30〜1:20 | デモ案件を入力する | 架空のWeb制作会社向けAI活用案件を入力 |
| 1:20〜2:10 | Sales Strategy確認を押す | 意思決定者、競合状況、勝ち筋、想定反論をAIが整理 |
| 2:10〜3:00 | Strategy Workspaceを操作する | AI案と営業担当編集の差分、Strategy Scoreを表示 |
| 3:00〜3:40 | Story候補とPresentation Toneを選ぶ | ROI重視、DX重視、差別化重視などから選択 |
| 3:40〜4:30 | Presentation Designer AIを見る | Layout候補、Before / After、Score改善を確認 |
| 4:30〜5:00 | Quality EngineとPPTX連携を説明する | 18カテゴリ評価、Auto Fix、PPTX Quality Summaryを説明 |

---

## 3. 10分デモ構成

### Step 1: ログイン

説明:

「Ready Crew Proposal AIは、案件入力から提案戦略、資料設計、品質評価までを一つの画面で扱うAI営業支援ツールです。」

期待表示:

- ホームまたはProposal Studioへ移動できる
- エラー表示がない

### Step 2: Proposal Studioを開く

説明:

「Version81では、従来の提案生成に加えて、Sales Strategy AI、Proposal Strategy Workspace、Presentation Designer AIを追加しています。」

期待表示:

- Prompt Builder
- Story Engine
- Designer
- Presentation Quality Engine

### Step 3: デモ案件を入力

`V81_DEMO_DATA.md` の「コピー用案件入力文」を貼り付けます。

説明:

「今回は、Web制作会社が中小企業向けにAI提案・問い合わせ対応を効率化する案件を想定します。」

期待表示:

- 入力が保持される
- 次工程へ進める

### Step 4: Sales Strategy確認

操作:

- 「Sales Strategy確認」を押す

説明:

「ここでは、資料を作る前に、誰に、何を、どの順番で伝えるべきかをAIが整理します。」

期待表示:

- Winning Strategy
- Decision Maker
- Competitive Position
- Expected Objections
- Proposal Position
- Presentation Tone
- Confidence
- Human Review

### Step 5: Proposal Strategy Workspace

操作:

- Winning StrategyまたはProposal Positionを少し編集する
- 差分表示を見る

説明:

「AI案をそのまま使うのではなく、営業担当者が編集してから後続工程へ渡せます。」

期待表示:

- 左: AI提案
- 中央: 営業担当編集
- 右: 評価・スコア
- 差分表示
- Strategy Score

### Step 6: 不足情報の確認

操作:

- 不足情報または確認事項を確認済みにする

説明:

「AIが推測している部分と、人間が確認すべき部分を分けて扱います。」

期待表示:

- 不足、仮説、確認必要、AI推定の区分
- 確認済み状態

### Step 7: Story候補を選ぶ

操作:

- ROI重視、DX重視、競合差別化重視などから1つ選ぶ

説明:

「同じ案件でも、経営者向け、現場向け、競合差別化向けで説明順が変わります。」

期待表示:

- 選択したStoryがStory Engineへ反映される

### Step 8: Presentation Toneを比較

操作:

- Executive、Consulting、Agency、Data Drivenなどを切り替える

説明:

「資料のトーンも、意思決定者と提案ポジションに合わせて選べます。」

期待表示:

- Toneごとの完成イメージ説明
- Designer AIの判断理由へ反映

### Step 9: Presentation Designer AI

操作:

- Layout候補を確認
- Before / Afterを確認
- 必要に応じて適用

説明:

「スライドごとに、Cover、Problem、Comparison、Timeline、EstimateなどのSlide Typeを見てLayoutを提案します。」

期待表示:

- 現在Layout
- Layout候補
- 変更理由
- 期待効果
- Presentation Score変化

### Step 10: Presentation Quality Engine

操作:

- Quality Scoreを見る
- Findingsを見る
- Auto Fixの修正前 / 修正後を確認する

説明:

「18カテゴリで資料品質を評価し、タイトル長、本文量、箇条書き数、図解不足、強調不足などを検出します。」

期待表示:

- 100点評価
- 改善理由
- Diagram Recommendation
- Content Fit
- Auto Fixの適用 / 却下

### Step 11: PPTX生成へ進む

操作:

- 必要に応じてPPTX生成ボタンを押す

説明:

「Version81では、画面で確認したQuality StateとLayout DecisionをPPTX生成リクエストへ渡します。」

期待表示:

- PPTX生成が成功する
- PPTX Quality Summaryが表示される

### Step 12: Completion Reportを見せる

操作:

- `V81_COMPLETION_REPORT.md` を開く

説明:

「実装したPhase、テスト結果、未実装範囲、Version82ロードマップを第三者向けに整理しています。」

### Step 13: まとめ

説明:

「Version81の価値は、AIが資料を作るだけではなく、営業担当者とAIが一緒に提案戦略と資料品質を完成させる点です。」

---

## 4. 失敗時の代替説明

| 失敗内容 | 代替手段 | 説明例 |
|---|---|---|
| Backendが起動しない | Completion Reportとデモ成果物を見せる | 「本日はローカル環境都合のため、生成済み成果物で流れを説明します。」 |
| Frontendが起動しない | スクリーンショットまたはMarkdown資料で説明 | 「画面構成はこの資料の画面一覧に沿って確認できます。」 |
| AI生成が遅い | デモデータと生成済みBriefを使う | 「外部AI待ち時間を避けるため、同じ入力から生成したサンプルで説明します。」 |
| PPTX生成に失敗 | Quality Engineまでをデモする | 「今回の主眼はStrategy、Designer、Qualityの連携です。PPTXは既存機能として回帰確認対象です。」 |
| Beautiful.aiが利用できない | Beautiful.aiは説明のみ | 「外部サービスのため、研修デモでは既存の連携状態と診断画面で確認します。」 |
| ブラウザ表示が崩れる | Markdown資料へ切り替える | 「提出資料側でPhaseと価値を説明します。」 |

---

## 5. 発表で避ける表現

- 「DBに保存できます」
  今回のStrategy Workspace編集内容は永続保存対象外です。

- 「複数人で同時編集できます」
  共同編集はVersion82以降です。

- 「Knowledge AIで過去提案を自動参照します」
  Knowledge AIはVersion82以降の候補です。

- 「外部AIを追加で呼び出しています」
  Version81の多くは既存フローと決定論的な補助ロジックを中心に構成しています。

---

## 6. 最後の一言

「Version81では、資料生成の前段に営業戦略レビューを置き、後段に資料品質評価を置くことで、AI生成を人間が業務で使える形へ近づけました。」
