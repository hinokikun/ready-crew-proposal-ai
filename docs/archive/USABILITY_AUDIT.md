# Usability Audit - Version 16.1

## 目的

AI営業秘書 / AI Workspace を、営業担当が迷わず毎日使える状態に近づけるための操作検証メモです。
新機能追加ではなく、既存機能の初期表示、導線、文言、レスポンシブ、アクセシビリティ、エラー時の分かりやすさを確認対象にしています。

## 主要シナリオ

### シナリオA: 提案書作成

- 開始地点: ログイン後ホーム
- 操作手順:
  1. 今日のAIブリーフィングとSales Copilotを確認する
  2. 案件メール貼り付け欄にReady Crew案件メール、議事録、URLを貼り付ける
  3. AI Workspaceが情報整理、提案書作成、レビュー、品質チェックへ進む
  4. 提出前品質ゲートを確認する
  5. 要約PPTをダウンロードする
- 完了条件: 要約PPTがダウンロード可能になり、提出前チェックリストが確認済み
- 想定エラー:
  - Backend未接続
  - OpenAI API上限
  - 入力不足
  - PPT生成失敗
  - 品質ゲート未完了によるダウンロード不可

### シナリオB: 修正依頼対応

- 開始地点: Sales Copilot、レビュー一覧、AI Workspace
- 操作手順:
  1. 修正依頼通知またはレビュー状態を確認する
  2. 上司コメントを確認する
  3. 「修正内容を反映」でAI営業・AIディレクターの改善方針を反映する
  4. 差分サマリーを確認する
  5. 再レビューを依頼する
- 完了条件: レビュー状態が review_requested に戻り、修正履歴が残る
- 想定エラー:
  - 権限不足
  - レビューID未取得
  - 再作成API失敗
  - 監査ログ保存失敗

### シナリオC: CRMで案件状況確認

- 開始地点: Sales Copilot、Action Center、詳細メニュー
- 操作手順:
  1. Quick Command またはショートカットからCRMを開く
  2. 案件名、顧客名、担当者、Project IDで検索する
  3. 案件状況、タイムライン、レビュー状態を確認する
  4. 営業担当がステータスを更新する
- 完了条件: 案件ステータス変更が保存され、履歴に残る
- 想定エラー:
  - 案件が0件
  - DB接続失敗
  - viewer権限による編集不可
  - 対象案件IDが存在しない

### シナリオD: Sales Copilotで今日やること確認

- 開始地点: ログイン後ホーム右側のSales Copilot
- 操作手順:
  1. AIおすすめアクションを確認する
  2. Quick Commandでレビュー、品質ゲート、CRMなどへ移動する
  3. AI ToDoを完了する
  4. 必要に応じて質問欄に「今日何からやればいい？」と入力する
- 完了条件: 推奨アクションの対象画面へ移動でき、ToDoが処理済みになる
- 想定エラー:
  - 移動先パネルが存在しない
  - admin専用機能がmemberに表示される
  - データ不足で推奨が固定値に見える

### シナリオE: 管理者確認

- 開始地点: adminログイン後ホーム
- 操作手順:
  1. 管理者メニューを開く
  2. 利用状況、レビュー、エラー、監査ログを確認する
  3. Product Analytics、Learning、Prompt Studioなどの改善分析を必要時だけ開く
  4. 問題があればリリース管理・運用準備チェックを確認する
- 完了条件: 管理者が利用状況とエラー傾向を把握できる
- 想定エラー:
  - 管理者パネルの初期読み込みが重い
  - 権限外ユーザーに管理項目が表示される
  - API未接続時に画面全体が落ちる

## 確認した画面

- ログイン画面
- ログイン後ホーム
- Real Operations Dashboard
- Sales Copilot
- AI Workspace
- 案件メール貼り付け欄
- 詳細メニュー
- 管理者メニュー
- CRM / Dashboard
- レビュー一覧
- 品質ゲート
- Product Analytics
- Prompt Studio
- Knowledge

## 修正済み

| 優先度 | 内容 | 修正 |
| --- | --- | --- |
| 高 | memberの初期画面に管理機能への入口が混ざる | QuickActions / Sales Copilotでadmin専用項目を非表示 |
| 高 | Sales CopilotのQuick Commandが閉じたdetails内へ移動できない | 親detailsを順番に開いてからスクロールするよう修正 |
| 高 | Knowledge / Analytics / Prompt Studioの移動先が曖昧 | 実在するadmin内パネルIDへ統一 |
| 中 | 案件なし時に0だけが並ぶ | 「案件メールを貼り付けて開始してください」などの空状態文言に変更 |
| 中 | 古い入力ガイドが初期表示で情報過多 | 折りたたみの「入力ガイド・詳細操作」へ移動 |
| 中 | 360px付近でカードやチャットが詰まりやすい | ダッシュボードとSales Copilotに折り返し・1カラム対応を追加 |
| 中 | フォーカス位置が分かりにくい | 主要ボタン・検索・Copilot入力へfocus-visibleを追加 |
| 低 | 通知への移動先がない | AI活動ログにnotifications-panel IDを追加 |

## 未修正 / 今後確認

| 優先度 | 内容 | 再現手順 | 推奨対応 |
| --- | --- | --- | --- |
| 高 | Playwright依存が未導入の環境ではE2Eを実行できない | `npm.cmd run test:e2e` | `npm.cmd install -D @playwright/test` と `npx playwright install chromium` を実行 |
| 中 | 一部管理画面はAPI未接続時にデータが空表示になる | Backend停止状態でadminメニューを開く | 各管理パネル単位のエラー境界と再試行を追加 |
| 中 | Sales Copilotの一部推奨は既存データからの推定 | 案件・利用ログが少ない状態で確認 | 実測値が不足する項目に「推定」ラベルを増やす |

## 仮実装 / デモ表示

- 平均提案時間: 「20〜30分」はデモ目安。実測Analytics蓄積後に更新します。
- AI自律率 / 人間介入率: 現時点では利用成功率からの推定です。
- Knowledge一致率: 詳細な類似度ではなく、履歴・Knowledge参照候補の有無からの表示です。
- 外部連携: OAuthや実メール取得は未実装。Dry Runのみです。
- Browser Use連携: 自動ログイン、自動送信、非公開情報取得は行いません。

## 空データ時の表示方針

- 案件なし: 「まだ案件がありません。案件メールを貼り付けて開始してください」
- レビューなし: 「レビュー待ちの案件はありません」
- 通知なし: 「現在、対応が必要な通知はありません」
- Analyticsなし: 「利用データが蓄積されると表示されます」
- AI活動ログなし: 「まだAI活動ログはありません」

## アクセシビリティ確認

- 入力欄はlabel配下に配置し、スクリーンリーダーで用途が分かる構造を維持
- 主要ボタン、検索、Copilot入力にfocus-visibleを追加
- 状態表示は色だけでなく文言を併記
- prefers-reduced-motionでアニメーション・スクロール挙動を軽減
- admin専用機能はmember/viewerの初期画面に表示しない

## E2Eテスト観点

- ログイン画面が表示される
- ログイン後にDashboardが表示される
- 案件入力欄へ入力できる
- memberに管理者メニューが表示されない
- adminに管理者メニューが表示される
- Sales CopilotのQuick Commandが対象画面へ移動する
- 存在しないページでアプリ全体が落ちない

## E2E実行手順

現時点のテスト定義は `frontend/e2e/app.spec.ts` にあります。
Playwright本体が未導入の環境では、以下を実行してからテストします。

```powershell
cd frontend
npm.cmd install -D @playwright/test
npx playwright install chromium
npm.cmd run test:e2e
```

今回のCodex環境では、npmキャッシュへの書き込み権限エラーにより `@playwright/test` の追加インストールは完了しませんでした。
`package.json` の `test:e2e` は `npx --yes @playwright/test@1.51.1 test` で実行するため、通常のWindowsローカル環境では依存取得後にそのまま起動できます。
