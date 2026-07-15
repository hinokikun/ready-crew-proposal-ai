# ProposalPilot Visual Guide

製品名: AI営業秘書

## ブランドカラー

### Primary

- Proposal Blue: `#1D4ED8`
- 用途: 主ボタン、現在ステップ、重要なリンク、強調表示
- 印象: 信頼、前進、業務効率

### Secondary

- Work Slate: `#334155`
- 用途: 見出し、本文、管理者画面、落ち着いた背景
- 印象: 実務的、安定、読みやすい

### Accent

- Pilot Green: `#16A34A`
- 用途: 完了、成功、チェック済み、品質ゲート完了
- 印象: 安心、安全、完了

### Support Colors

- Warning Amber: `#D97706`
- Error Red: `#DC2626`
- Surface Gray: `#F8FAFC`
- Border Gray: `#CBD5E1`
- White: `#FFFFFF`

## 推奨フォント

### 日本語

- Noto Sans JP
- BIZ UDPGothic
- system-ui fallback

### 英数字

- Inter
- Segoe UI
- system-ui

## アイコン方針

- 線幅が揃ったシンプルなアイコンを使う
- ボタン内は可能な限りアイコン + 短いラベルにする
- 意味が曖昧なアイコンにはtooltipを付ける
- AIを過度に擬人化したアイコンは避ける
- 営業、書類、チェック、出力、履歴、通知の意味が直感的に伝わるものを使う

## 写真イメージ

- 営業担当がPCで提案準備している自然な業務風景
- チームで提案書を確認している会議シーン
- 清潔感のあるオフィス
- 実務的なデスク、ノートPC、資料
- 避けるもの: 過度な未来都市、抽象的すぎるAI表現、派手なSF表現

## 余白ルール

- 基本単位: 8px
- 小さな部品間: 8px
- カード内余白: 16pxから24px
- セクション間: 32pxから48px
- モバイルでは横余白16pxを基本とする

## 角丸

- 通常カード: 8px
- 入力欄: 8px
- 小ボタン: 8px
- モーダル: 12px
- 過度に丸いpill形状は多用しない

## ボタンデザイン

### Primary Button

- 背景: Proposal Blue
- 文字: White
- 用途: 各画面で最も重要な1操作
- 例: この内容で提案書を作る、提出前チェックを完了する

### Secondary Button

- 背景: White
- 枠線: Border Gray
- 文字: Work Slate
- 用途: 戻る、詳細を見る、コピー

### Danger Button

- 背景: White
- 枠線: Error Red
- 文字: Error Red
- 用途: 無効化、削除、緊急停止

### Disabled Button

- 背景: `#E2E8F0`
- 文字: `#64748B`
- 必ず近くに理由を表示する
