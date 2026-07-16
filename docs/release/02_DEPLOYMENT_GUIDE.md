# ProposalPilot デプロイ手順

対象製品: ProposalPilot / AI営業秘書
本番Frontend URL: 要入力
本番Backend URL: 要入力
独自ドメイン: 要入力

## 1. 全体構成

- GitHub: ソースコード管理とGitHub Actions
- Vercel: Frontend本番配信
- Render: Backend本番稼働
- Google Analytics: 公開サイト計測
- Google Search Console: 検索登録とサイト状態確認
- DNS: 独自ドメイン管理

## 2. GitHub

1. `main` ブランチに公開対象commitをpushする
2. GitHub Actionsを開く
3. 最新workflow runの対象commitを確認する
4. Backend pytest、Frontend build、E2E、Smoke Testが成功していることを確認する
5. 失敗した場合は、本番デプロイ確認へ進まず原因を記録する

確認項目:

- 最新commit: 要入力
- GitHub Actions URL: 要入力
- Release tag: 要入力

## 3. Vercel

### 3.1 基本設定

| 項目 | 設定 |
| --- | --- |
| Project | 要入力 |
| Root Directory | `frontend` |
| Production Branch | `main` |
| Build Command | 要入力 |
| Output Directory | 要入力 |
| Install Command | 要入力 |

### 3.2 環境変数

値は管理画面にのみ保存し、ドキュメントやログへ記録しないでください。

| 変数名 | 用途 | 状態 |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Render Backend URL | 要入力 |
| `NEXT_PUBLIC_APP_ENV` | 環境名 | 要入力 |
| `NEXT_PUBLIC_BUILD_VERSION` | 表示用ビルド情報 | 要入力 |

### 3.3 独自ドメイン

1. VercelのDomainsへ独自ドメインを追加する
2. DNS側でVercelが指定するCNAMEまたはAレコードを設定する
3. SSL証明書が有効になるまで待つ
4. `https://` でアクセスできることを確認する
5. wwwあり / なしの正規化方針を確認する

独自ドメイン: 要入力
正規URL: 要入力

## 4. Render

### 4.1 基本設定

| 項目 | 設定 |
| --- | --- |
| Service Name | 要入力 |
| Branch | `main` |
| Runtime | 要入力 |
| Build Command | 要入力 |
| Start Command | 要入力 |

### 4.2 環境変数

値はRender環境変数としてのみ設定してください。値をGit、ログ、ドキュメントへ保存しないでください。

| 変数名 | 用途 | 状態 |
| --- | --- | --- |
| `APP_AUTH_SECRET` | 認証署名 | 要入力 |
| `DATABASE_URL` | DB接続 | 要入力 |
| `OPENAI_API_KEY` | OpenAI API接続 | 要入力 |
| `BEAUTIFUL_AI_API_KEY` | Beautiful.ai API接続 | 要入力 |
| `BEAUTIFUL_AI_API_MODE` | Beautiful.ai APIモード | 要入力 |
| `BEAUTIFUL_AI_THEME_ID` | Beautiful.aiテーマ指定 | 要入力 |
| `BEAUTIFUL_AI_WORKSPACE_ID` | Beautiful.ai Workspace指定 | 要入力 |
| `MAINTENANCE_MODE` | メンテナンス制御 | 要入力 |
| `PILOT_MODE` | 試験運用制御 | 要入力 |

### 4.3 Health確認

以下を確認します。

- Backend URL: 要入力
- `/health`
- `/health/ready`
- `db_connected`
- `migration_ready`
- `database_ready`
- `maintenance_mode`
- Beautiful.ai route登録

## 5. Google Analytics

1. Google Analyticsでプロパティを作成する
2. 測定IDを取得する
3. LPまたは公開サイト側へ測定IDを設定する
4. リアルタイム計測でアクセスが記録されることを確認する

測定ID: 要入力
管理者: 要入力

## 6. Google Search Console

1. Search ConsoleでドメインまたはURLプレフィックスを追加する
2. DNS確認またはHTMLタグ確認を設定する
3. `sitemap.xml` を送信する
4. インデックス登録状況を確認する

Search Console Property: 要入力

## 7. OGP / favicon / robots / sitemap

- [ ] OGP title
- [ ] OGP description
- [ ] OGP image
- [ ] favicon
- [ ] `robots.txt`
- [ ] `sitemap.xml`
- [ ] canonical URL
- [ ] 404ページ表示

## 8. Rollback

本番で重大障害が発生した場合は、原則として履歴を残すため `git revert` を使用します。

1. 障害の原因commitを確認する
2. `git revert <commit>`
3. `git push origin main`
4. GitHub Actions成功を確認する
5. Vercel / Renderの再デプロイを確認する
6. `/health` と主要動線を確認する

`reset --hard` やforce pushは使用しません。
