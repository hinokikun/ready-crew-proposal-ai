# Pilot Admin Guide

社内試験導入中に管理者が行う作業をまとめます。

## 1. Pilot対象ユーザーを設定する

1. adminでログイン
2. 管理者メニューを開く
3. ユーザー管理を開く
4. 対象ユーザーを追加
5. 「Pilot対象にする」を押す

`PILOT_MAX_USERS` を超える人数はPilot対象にできません。adminはPilot対象外でもログインできます。

## 2. Pilot Dashboardを確認する

管理者メニューの「Pilot Dashboard」を開き、以下を確認します。

- 対象ユーザー数
- 利用開始済み人数
- 今週アクティブ人数
- 提案作成数
- 成功率
- エラー件数
- フィードバック件数
- 未利用ユーザー
- 残り日数

## 3. メンテナンスに切り替える

重大な問題がある場合は Render の環境変数を変更します。

```text
MAINTENANCE_MODE=true
```

メンテナンス中もログイン、履歴確認、CRM閲覧、管理者メニュー、ヘルスチェックは利用できます。新規提案書作成、PPT/PDF新規作成、Orchestrator新規実行は停止します。

## 4. クラウドスモークテスト

GitHub Actions の `Cloud deployment smoke test` を手動実行します。

必要なSecrets:

```text
SMOKE_FRONTEND_URL
SMOKE_BACKEND_URL
SMOKE_TEST_EMAIL
SMOKE_TEST_PASSWORD
SMOKE_VIEWER_EMAIL
SMOKE_VIEWER_PASSWORD
SMOKE_DISABLED_EMAIL
SMOKE_DISABLED_PASSWORD
SMOKE_EXPECT_PILOT_MODE
```

`SMOKE_DISABLED_EMAIL` はPilot対象外ユーザーにしてください。Pilot Mode中にログイン拒否されることを確認します。

ローカルから実行する場合:

```powershell
$env:FRONTEND_URL="https://your-app.vercel.app"
$env:BACKEND_URL="https://your-api.onrender.com"
$env:SMOKE_TEST_EMAIL="pilot@example.com"
$env:SMOKE_TEST_PASSWORD="..."
$env:SMOKE_EXPECT_PILOT_MODE="true"
python scripts/smoke_test.py
```

パスワードやトークンは出力されません。

## 5. Pilot終了

Pilot Dashboard の「試験導入を終了する」から集計レポートを作成します。

終了時に行うこと:

- 対象ユーザーをPilot対象外にする
- 集計レポートをコピーする
- フィードバックを確認する
- 次回改善案を決める

レポートには顧客本文、生成本文、APIキー、パスワード、トークンを含めません。
