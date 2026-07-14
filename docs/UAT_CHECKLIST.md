# Version 20.3 UATチェックリスト

このチェックリストは、Version 20.1までの実装をブラウザで確認するためのものです。Version 20.3では新しい営業機能やBackend APIは追加せず、UAT実施支援、結果保存、再現情報整理、△ / ×項目の修正準備を目的にしています。

## UATでの実データ利用ルール

原則として架空データのみを使用してください。

使用してよい例:
- 会社名: 株式会社サンプル
- 担当者: テスト担当
- URL: `https://example.com`
- 予算: 300万円
- 納期: 3か月

入力禁止:
- 実顧客名
- 実担当者名
- 実メールアドレス
- 実電話番号
- Password
- APIキー
- Token
- 機密案件本文
- 顧客の未公開情報

## UAT用テスト案件文

以下を案件入力欄へ貼り付けて確認してください。

```text
株式会社サンプルがコーポレートサイトのリニューアルを検討しています。
目的は問い合わせ増加と採用強化です。
現行サイトは情報が古く、スマートフォンで見づらい状態です。
想定ページ数は20ページ、CMS導入希望、問い合わせフォームあり、
予算は300万円、公開希望は3か月後です。
競合サイトは https://example.com/competitor を想定しています。
担当者はテスト担当、決裁者は要確認です。
```

## UAT結果の保存方針

UAT結果はBackendへ送信せず、まずはブラウザのlocalStorageに保存します。

保存単位:
- `user_id`
- `organization_id`
- `workspace_id`
- Frontend Build Version
- Backend Version

保存内容:
- `checklist_item_id`
- `result`: `pass` / `partial` / `fail` / `untested`
- `comment`
- `checked_at`
- `checked_by`

コメントにAPIキー、Password、Token、顧客本文全文、個人情報、機密情報を入力しないでください。

## 完成度計算式

完成度は以下で計算します。

- ○ = 1.0
- △ = 0.5
- × = 0
- 未確認 = 0

計算式:

```text
完成度 = (○件数 * 1.0 + △件数 * 0.5) / チェック項目数 * 100
```

重大項目が1件でも×の場合は「本番利用不可」とします。重大不具合0件かつ完成度90%以上の場合のみ「条件付きで試験利用可能」と表示します。自動的に正式リリース可とは判定しません。

## UAT実施手順

1. 管理者でログインする。
2. 画面上部の「ブラウザ確認モードON」を押す。
3. UAT状態カードで以下を確認する。
   - Frontend Build Version
   - Frontend Git Commit
   - Backend Version
   - Backend Git Commit
   - Migration Ready
   - Database Ready
   - Health
   - Maintenance
   - OpenAI Mode
   - Beautiful.ai Enabled
   - Beautiful.ai Configured
   - Beautiful.ai Route
   - Beautiful.ai Mock
   - Organization
   - Workspace
   - Role
4. 「確認ジャンプ」から各画面へ移動する。
5. 下記チェック項目を確認し、○ / △ / × とコメントを入力する。
6. 「Markdownをコピー」で結果を共有する。

## チェック項目

### 1. 管理者ログイン

確認内容:
- adminでログインできる。

期待結果:
- Dashboardが表示される。
- 管理者メニューが表示される。
- ブラウザ確認モードが表示される。

### 2. 一般利用者ログイン

確認内容:
- memberまたはuserでログインできる。

期待結果:
- Dashboardが表示される。
- 管理者メニューとブラウザ確認モードは表示されない。

### 3. Dashboard

確認内容:
- KPI
- Sales Copilot
- AI Workspace導線

期待結果:
- 「今日やること」が分かる。
- 空データ時も分かりやすい案内が表示される。

### 4. Organization / Workspace表示

確認内容:
- 現在のOrganizationとWorkspaceが表示される。

期待結果:
- Organization名、Workspace名、Roleが確認できる。

### 5. Workspace切替

確認内容:
- 権限のあるWorkspaceへ切り替える。

期待結果:
- 切替後、対象Workspaceのデータだけが表示される。
- 他Organizationのデータは参照できない。

### 6. 案件入力

確認内容:
- UAT用テスト案件文を貼り付ける。

期待結果:
- 入力欄に貼り付けられる。
- AIが整理を開始できる。

### 7. AI提案書生成

確認内容:
- 提案書作成まで進める。

期待結果:
- AI Workspaceが進行する。
- 生成結果が表示される。
- エラー時は日本語で次の行動が表示される。

### 8. 要約PPTX

確認内容:
- 要約PowerPointをダウンロードする。

期待結果:
- 要約PPTXが作成される。
- 品質ゲート未完了時はロックまたは警告が表示される。

### 9. 詳細PPTX

確認内容:
- 通常版PowerPointをダウンロードする。

期待結果:
- 詳細PPTXが作成される。
- 失敗時は再試行案内が表示される。

### 10. 見積PDF

確認内容:
- 見積PDFをダウンロードする。

期待結果:
- PDFが作成される。
- 失敗時は「PDF生成失敗」と次にやることが表示される。

### 11. Quality Gate

確認内容:
- 提出前確認を実施する。

期待結果:
- 会社名、金額、納期、AI推測、上司レビューなどを確認できる。
- 完了後、主要ダウンロードが可能になる。

### 12. Beautiful.ai Status

確認内容:
- Beautiful.ai Status Cardを確認する。

期待結果:
- Enabled、Configured、Route、Mock、Backend Versionが分かる。
- Backend到達とBeautiful.ai実生成成功を混同しない表現になっている。

### 13. Beautiful.ai新規生成

確認内容:
- Beautiful.ai作成ボタンを押す。

期待結果:
- 条件を満たすと作成できる。
- Disabledの場合は、どの条件が不足しているか分かる。

### 14. Presentation Review

確認内容:
- 提案書レビューを実行する。

期待結果:
- ストーリー、説得力、ROI、競合比較などの評価が表示される。

### 15. Proposal Optimization

確認内容:
- TOP5改善を確認する。

期待結果:
- 改善内容、期待効果、信頼度、工数、理由が表示される。
- 推測値であることが分かる。

### 16. Revision v2

確認内容:
- Revision v2を作成する。

期待結果:
- v1との差分が表示される。
- 追加、削除、修正が区別される。

### 17. Beautiful.ai Revision

確認内容:
- RevisionをBeautiful.ai向けに再生成する。

期待結果:
- 構成・見出し・CTAなどの修正として扱われる。
- Beautiful.aiのデザイン品質を壊さない設計になっている。

### 18. Best Practice

確認内容:
- Best Practice Libraryを確認する。

期待結果:
- 成功パターンが表示される。
- 本文全文や顧客情報が保存・表示されていない。

### 19. Analytics

確認内容:
- Product Analyticsを確認する。

期待結果:
- 管理者のみ確認できる。
- データなしの場合は空状態が分かりやすい。

### 20. 権限制御

確認内容:
- admin / manager / member / user / viewerの表示差を確認する。

期待結果:
- viewerは生成・編集・承認不可。
- member/userは通常利用のみ。
- admin/manager以外は管理者機能を利用できない。

### 21. Organization / Workspace分離

確認内容:
- 他Organizationまたは他Workspaceのデータ参照を試す。

期待結果:
- Backend API側でも拒否される。
- 画面に他Workspaceの案件やKnowledgeが混在しない。

### 22. モバイル表示

確認内容:
- 360px、768px、1024px、1440pxで確認する。

期待結果:
- 文字が1文字ずつ折り返されない。
- 横スクロールが発生しない。
- Sales CopilotやUATパネルが本文を圧迫しない。

### 23. エラー表示

確認内容:
- Maintenance、429、404、500を確認する。

期待結果:
- 画面全体が落ちない。
- 日本語で原因と次にやることが表示される。
- APIキーやDATABASE_URLなどの秘密情報が表示されない。

### 24. Maintenance

確認内容:
- Maintenance Modeの表示を確認する。

期待結果:
- 停止対象と利用可能な機能が分かる。
- ログイン、CRM閲覧、履歴閲覧、Pilot Dashboard、監査ログ、`/health` は利用できる。

### 25. Health

確認内容:
- Health状態を確認する。

期待結果:
- Backend、DB、OpenAI Mode、PPTX、PDFの状態が分かる。
- 秘密情報は表示されない。

### 26. Migration Ready

確認内容:
- Migration状態または取得可否を確認する。

期待結果:
- 取得できない場合は「未取得」と表示され、不一致や異常と断定しない。

## △ / ×項目の共有テンプレート

△または×が出た場合は、以下を共有してください。推測で修正せず、再現できた不具合だけを最小修正します。

```text
項目:
結果: △ / ×
再現手順:
期待結果:
実際の結果:
Role:
Organization:
Workspace:
Browser:
Frontend Version:
Backend Version:
request_id:
Render error_type:
画面スクリーンショット:
```
## Version 23.1 追加確認: ログイン入口分離

1. 利用者ログインが初期表示されること。
   - 期待結果: `member` / `viewer` がログインでき、管理者メニューは表示されない。
2. 管理者ログインへ切り替えられること。
   - 期待結果: `admin` / `manager` がログインでき、管理者メニューを利用できる。
3. `admin` が利用者ログインを選ぶこと。
   - 期待結果: 「管理者ログインからログインしてください」と表示される。
4. `member` が管理者ログインを選ぶこと。
   - 期待結果: 「このアカウントには管理者権限がありません」と表示される。
5. ログアウト後の入口復元。
   - 期待結果: 直前に利用したログイン入口が選択された状態で表示される。
## Version 23.0 Simple Guided UI追加確認

1. 一般利用者でログインし、通常モードが初期表示されること
2. 7ステップのナビゲーションが表示されること
3. STEP 1で案件情報入力欄、サンプルを使う、使い方を見るが表示されること
4. STEP 2で案件整理、提案作成、品質確認、スケジュール確認、最終確認が表示されること
5. STEP 3で案件概要、課題、提案方針、スケジュール、見積概要、注意事項、AI推測項目が表示されること
6. STEP 4で「提出前チェックを完了する」ボタンが常に見えること
7. 未チェック時に「あと○項目の確認が必要です」と表示されること
8. 全チェック後に提出前チェック完了ボタンが有効化されること
9. 完了後に出力方法を選べること
10. Beautiful.aiが押せない時、日本語の理由が表示されること
11. 一般利用者にGit Commit、Backend Version、Status APIなどの技術診断が表示されないこと
12. adminで詳細モードをONにすると管理者向け診断と管理者メニューが表示されること
13. 360px幅で入力欄と主ボタンが見えること
