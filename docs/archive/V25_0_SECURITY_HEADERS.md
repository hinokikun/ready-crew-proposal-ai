# Version 25.0 Security Headers

## 目的

Render Backend から返す API / health レスポンスに、本番運用に必要な基本セキュリティヘッダーを付与します。

## 追加ヘッダー

| Header | 値 | 目的 |
| --- | --- | --- |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing の抑止 |
| `X-Frame-Options` | `DENY` | clickjacking 対策 |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer 情報の過剰送信抑止 |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | 不要なブラウザ機能の無効化 |
| `Cross-Origin-Opener-Policy` | `same-origin` | Window 分離 |
| `Cross-Origin-Resource-Policy` | `cross-origin` | Vercel から Render API を利用する構成を維持 |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'` | API レスポンスの実行抑止 |
| `Cache-Control` | `no-store` | API / health のキャッシュ抑止 |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | production 環境のみ HTTPS 固定 |

`/docs`、`/redoc`、`/openapi.json` は Swagger UI 表示を壊さないため、CSP の適用対象から外します。

## CORS 方針

- production では `localhost` と `127.0.0.1` を許可しません。
- production では `*` を許可しません。
- local / dev / test ではローカル開発用 origin を許可します。
- `CORS_ORIGINS` には Vercel の本番 URL を明示します。
- `CORS_ORIGIN_REGEX` に `.*` や `^.*$` を指定した場合、production では無効化します。

## Render に必要な設定

```text
APP_ENV=production
CORS_ORIGINS=https://<your-vercel-production-domain>
```

複数の Vercel URL を使う場合はカンマ区切りにします。

## 確認項目

- Vercel 本番 URL から API が呼べること
- `localhost` origin が production で許可されないこと
- `/health` に `X-Request-ID` が付与されること
- API キーや接続文字列がヘッダーやレスポンスに出ないこと
