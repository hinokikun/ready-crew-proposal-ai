# Version 23.1 Vercel Verification Guide

目的: GitHub push 後、Vercel 本番 Frontend が最新状態で配信されているか確認する手順です。

## 確認項目

1. 最新 Deployment が `Ready` であること
2. `Production` Deployment になっていること
3. branch が `main` であること
4. commit が GitHub 最新 commit と一致していること
5. Root Directory が `frontend` であること
6. `NEXT_PUBLIC_API_URL` が Render Backend URL を指していること
7. Serverless Function 上限エラーがないこと
8. Build Logs にエラーがないこと
9. 本番 URL を Ctrl + F5 で更新して表示確認すること

## 手順

1. Vercel Dashboard を開きます。
2. 対象 project を選択します。
3. `Deployments` を開きます。
4. 一番上の deployment が最新であることを確認します。
5. 状態が `Ready` であることを確認します。
6. `Production` の表示があることを確認します。
7. commit hash が GitHub の最新 commit と一致していることを確認します。
8. deployment の `Build Logs` を開きます。
9. `Module not found`、TypeScript error、Serverless Function 上限エラーがないことを確認します。

## Root Directory

Vercel の設定で Root Directory は次の値を想定します。

```text
frontend
```

違っている場合:

- Next.js build 対象がずれる可能性があります。
- `package.json` が見つからない可能性があります。

## NEXT_PUBLIC_API_URL

Vercel Environment Variables で確認します。

期待:

- Render Backend の URL を指していること
- 末尾の slash 有無で壊れていないこと
- localhost を指していないこと

値そのものはこのドキュメントへ貼り付けないでください。

## Serverless Function 上限エラー

Vercel Hobby では Serverless Functions の数に制限があります。

確認するエラー例:

```text
No more than 12 Serverless Functions can be added to a Deployment
```

Version 23.1 時点の想定:

- `frontend/app/**/route.ts`: 0 件
- Frontend 側 Serverless Functions 想定: 0

## 本番 URL 表示確認

1. Vercel の Production URL を開きます。
2. `Ctrl + F5` で強制更新します。
3. ログイン画面が表示されることを確認します。
4. admin / member でログインし、Guided Flow が表示されることを確認します。

## 失敗時に見る場所

- Vercel Deployment Details
- Build Logs
- Environment Variables
- GitHub Actions の該当 commit
- Render `/health`
- Browser DevTools Network
