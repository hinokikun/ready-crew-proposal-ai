# Simple Guided UI Spec

Version 23.0では、新しい営業機能を追加せず、一般利用者の初期画面を「次へ」で進める7ステップへ整理します。

## 変更前

1. Dashboard、AI Workspace、出力、管理者向け情報が同じ画面に並ぶ
2. Quality Gateの完了ボタンが見つけにくい
3. Beautiful.aiが押せない時、技術条件が多く原因を判断しにくい
4. Product Analytics、Prompt Studio、Learningなど管理者向け情報が一般画面に混ざる

## 変更後

1. 一般利用者は通常モードで7ステップだけを見る
2. 管理者は詳細モードをONにすると診断、UAT、管理者メニューを見られる
3. Quality Gateは「提出前チェック」と表示する
4. Beautiful.aiの無効理由は日本語の短文で表示する
5. Backend API、DB、権限、出力内容は変更しない

## 一般利用者の初期表示

- 今日やること
- 新しい案件を始める
- 作業中の案件
- 最近作成した提案書
- 進行中のステップ
- 案件情報入力欄

## 通常モードで隠す情報

- Git Commit
- Build Time
- Backend Version
- Migration Version
- request_id
- Status API
- Route found
- Configured
- Mock
- Prompt Studio
- Learning Dashboard
- Queue Monitor
- Audit Log
- Integration内部設定
- 管理用診断カード

## 受け入れ条件

- 次に押す主ボタンが常に1つ分かる
- 提出前チェックの完了方法が画面上で分かる
- Beautiful.aiが押せない理由が日本語で分かる
- 一般利用者に技術情報を見せない
- 管理者機能が一般フローに混ざらない
- 既存APIとDBを変更しない
