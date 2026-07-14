# Version 23.1 Render Verification Guide

目的: GitHub push 後、Render Backend が最新状態で起動しているか確認する手順です。

## 確認 URL 例

```text
https://ready-crew-proposal-ai.onrender.com/health
https://ready-crew-proposal-ai.onrender.com/health/ready
```

## 確認項目

1. 最新 Deploy が `Live` であること
2. Git commit が GitHub 最新 commit と一致していること
3. Logs に `Application startup complete` があること
4. `/health` が応答すること
5. `/health/ready` が応答すること
6. `db_connected` が正常であること
7. `migration_ready` が正常であること
8. `maintenance_mode` が意図した状態であること
9. `mock_ai` が意図した状態であること
10. Beautiful.ai route が登録されていること

## Render Dashboard 手順

1. Render Dashboard を開きます。
2. Backend service を選択します。
3. `Events` または `Deploys` を開きます。
4. 最新 deploy が `Live` であることを確認します。
5. deploy の commit hash が GitHub の最新 commit と一致していることを確認します。
6. `Logs` を開きます。
7. `Application startup complete` を確認します。

## /health 確認

ブラウザで次を開きます。

```text
https://ready-crew-proposal-ai.onrender.com/health
```

確認すること:

- APIキーや接続文字列が表示されないこと
- `db_connected` が確認できること
- `db_type` など安全な情報だけが表示されること
- Beautiful.ai の route 状態が分かる場合は確認すること

## /health/ready 確認

ブラウザで次を開きます。

```text
https://ready-crew-proposal-ai.onrender.com/health/ready
```

確認すること:

- `ready` 相当の状態であること
- migration が必要な状態で止まっていないこと
- maintenance 中かどうかが分かること

## Beautiful.ai status について

Beautiful.ai status はログイン必須 API です。

ブラウザで直接アクセスして次のような表示になる場合があります。

```text
ログインが必要です
```

これは route が存在し、認証で止められている確認になる場合があります。

404 の場合:

- route が登録されていない
- Render が古い commit を動かしている
- Backend の include_router が漏れている
- path が間違っている

## 失敗時に見る場所

- Render Deploy Logs
- GitHub 最新 commit
- GitHub Actions
- Environment Variables
- `/health`
- `/health/ready`
- Frontend の `NEXT_PUBLIC_API_URL`
