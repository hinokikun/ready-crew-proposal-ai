# Version 37.0 Presentation Design

## 目的

ProposalPilot / AI営業秘書のPowerPoint出力を、文章中心の生成物から営業資料として読みやすい編集可能なプレゼンへ改善する。

## デザイン原則

- 1スライド1メッセージを優先する。
- 詳細版は標準生成で20から25ページ程度に収める。
- 要約版は8から12ページ程度に収める。
- 本文を長文で詰め込まず、カード、工程図、構成図、KPIカード、見積カードで見せる。
- PowerPoint上で編集できる図形、テキスト、表を使う。スライド全体の画像化は禁止。
- ブランド表記は各ページに `ProposalPilot / AI営業秘書` として表示する。
- Web案件以外ではサイトマップ風の表示を避け、入力、AI判定、人の確認、連携、運用改善の構成図として表示する。

## ブランド

- Primary: Proposal Blue `#155EEF`
- Base: Deep Navy `#102A43`
- Accent: Cyan `#06AED4`, Emerald `#12B76A`, Purple `#7A5AF8`
- Background: `#F8FAFC`
- Text: `#1D2939`, `#667085`
- Border: `#D0D5DD`
- Font: `Noto Sans JP`

## 追加した設計層

`backend/app/services/pptx_design/` に、PPTX専用のデザイン部品と検査ロジックを追加した。

- `theme.py`: ブランドカラーとレイアウト名
- `components.py`: KPIカード、工程カード、構成図、見積カード、次アクションカード
- `validators.py`: 空白スライド、ブランド欠落、図形不足、テキストのみスライドの検査

## 詳細版の整理

Version 36以前は、各本文スライドの前に章扉が差し込まれ、標準提案書が長くなりやすかった。
Version 37では本文スライド中心へ整理し、AI出力が過剰に長い場合は重複タイトルを除外し、重要な章を優先して25ページ以内に収める。

## カテゴリ別表示

- AI-OCR、画像認識、RPA、CRM/SFA、汎用案件は業務導入型の構成図を使う。
- Web案件はSEO、CMS、サイトマップなどのWeb固有表現を維持する。
- 見積項目は既存のカテゴリ別見積ロジックを使い、Web制作見積が非Web案件へ混入しないようにする。
