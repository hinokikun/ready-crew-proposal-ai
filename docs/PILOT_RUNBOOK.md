# AI営業秘書 Pilot Runbook

社内3〜5名で試験利用するときの運用手順です。顧客本文、生成本文、APIキー、パスワードはRunbookやIssueに記録しません。

## Pilot開始前確認

- GitHub Actionsが成功している
- Vercel Buildが成功している
- Render `/health` が `status: ok` を返す
- 初期管理者でログインできる
- admin / manager / member / viewer の権限を確認した
- Maintenance Modeが無効である
- Pilot対象者が3〜5名に絞られている
- 提出前品質ゲート、上司レビュー、要約PPT、詳細PPT、見積PDFを1回ずつ確認した

## Render環境変数

- `OPENAI_API_KEY`
- `USE_MOCK_AI`
- `APP_AUTH_SECRET`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `DATABASE_URL`
- `PILOT_MODE`
- `PILOT_START_DATE`
- `PILOT_END_DATE`
- `PILOT_MAX_USERS`
- `MAINTENANCE_MODE`
- `CORS_ORIGINS` または `CORS_ORIGIN_REGEX`

APIキーやDATABASE_URLの値そのものは画面、Issue、Runbookへ貼り付けません。

## Vercel確認

- Root Directoryが `frontend` になっている
- `NEXT_PUBLIC_API_URL` がRender Backend URLを指している
- Build Logsに `Module not found` がない
- 公開URLからログイン画面が開く

## GitHub Actions確認

- `backend-test`
- `frontend-build`
- `lint-check`

失敗した場合は該当Jobのログを確認し、修正後に再実行します。pytest未実行で成功扱いにしません。

## Cloud Smoke Test

1. 管理者でログイン
2. `/health` を確認
3. サンプル案件を貼り付ける
4. AI Workspaceが進むことを確認
5. 提案書作成
6. 提出前品質ゲート
7. 要約PPT、詳細PPT、見積PDFを確認
8. Pilot Dashboardを開く
9. フィードバックを送信

## 試験利用者登録

1. 管理者メニューを開く
2. ユーザー管理で member を作成
3. Pilot対象にする
4. 初回ログイン手順を案内する
5. 顧客の機密情報、個人情報、パスワードを入力しないよう説明する

## 初日の確認

- ログインできた人数
- 案件メール貼り付けまで進めた人数
- 提案書作成まで進めた人数
- 要約PPTをダウンロードできた人数
- エラーや迷いが出た画面
- フィードバック入力の有無

## 毎日の確認

- Pilot Dashboardの利用率、成功率、重大エラー数、未解決Issue数
- 重大障害候補の有無
- 未解決Issueの担当者
- フィードバック平均
- Maintenance Modeが不要に有効化されていないか

## 重大障害時の停止

重大障害候補がある場合、管理者がPilot DashboardからMaintenance Modeを有効化します。

停止されるもの:

- 新規提案書作成
- PPT/PDF新規生成
- Orchestrator新規実行

停止後も利用可能なもの:

- ログイン
- CRM閲覧
- 履歴閲覧
- Pilot Dashboard
- Issue管理
- 監査ログ
- `/health`

環境変数 `MAINTENANCE_MODE=true` が設定されている場合は、画面設定より優先されます。

## Issue登録

- 顧客名、案件本文、生成本文は書かない
- 再現手順は短く書く
- 同じ内容がある場合は既存Issueを更新する
- critical/high は担当者を決める
- 解決時は resolution_note に対応内容だけを書く

## Pilot終了判定

Pilot Dashboardの終了判定で以下を確認します。

- 対象者の80%以上が利用
- 提案書作成成功率90%以上
- critical障害0件
- 使いやすさ平均4.0以上
- 実務利用可能評価70%以上
- 時間短縮実感70%以上

判定:

- 合格
- 条件付き合格
- 延長推奨
- 中止推奨

## Pilot終了レポート

管理者コメントを入力し、Pilot終了レポートを作成します。

レポートには以下を含めます。

- 実施期間
- 対象人数、実利用人数、利用率
- 提案書作成数、成功率、平均処理時間
- エラー件数
- フィードバック集計
- 発生Issue、解決済みIssue、未解決Issue
- 継続利用意向
- 正式導入可否
- 次回改善項目

顧客本文、生成本文、APIキー、パスワードは含めません。

## Pilot終了後のデータ処理

管理者は対象件数を確認してから、確認文字列 `PILOT` を入力して処理します。

- 集計データのみ保持
- Pilotイベントを匿名化して保持
- Pilotイベントを削除
- Pilotフィードバックを匿名化
- テストユーザーを無効化

本番CRM、案件、Knowledge、監査ログは削除対象外です。
