# Dependency Review

## Backend

| Dependency | 用途 | Review |
| --- | --- | --- |
| FastAPI / uvicorn | API runtime | 維持 |
| openai | 既存Proposal生成 | 維持 |
| pydantic v1 | API schema | 維持。v2移行は別Versionで検討 |
| python-pptx | PPTX生成・検証 | 維持 |
| reportlab | PDF生成 | 維持 |
| SQLAlchemy / alembic | DB / migration | 維持 |
| psycopg | PostgreSQL対応 | 継続使用想定 |
| pytest / httpx | backend test | 維持 |

## Frontend

| Dependency | 用途 | Review |
| --- | --- | --- |
| Next.js | Frontend runtime | 維持 |
| React | UI | 維持 |
| lucide-react | icon | 維持 |
| Playwright | E2E | 維持 |
| TypeScript | 型検査 | 維持 |

## 更新しなかった理由

Version55はProduction Hardeningであり、依存更新による挙動変化を避けた。依存更新はVersion56以降で、テスト計画とRollback計画を用意して実施する。

## 提案

- Pydantic v2移行調査
- Next.js minor更新の影響調査
- pytest一時ディレクトリ運用の整理
- lockfile監査とDependabot等の導入検討
