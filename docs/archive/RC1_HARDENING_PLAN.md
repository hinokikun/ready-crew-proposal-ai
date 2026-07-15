# v1.0 RC1 Priority A Hardening Plan

作成日: 2026-07-11  
根拠: `docs/PRODUCTION_AUDIT.md` の Priority A

## 対象範囲

新機能は追加しません。正式リリース前に必要なPriority Aだけを対象にします。

## Priority A抽出結果

| # | 問題 | 想定リスク | 対象ファイル | 修正方針 | テスト方法 | 完了条件 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | リリース対象差分・不要ファイルが多い | 意図しない生成物やローカルDBがGitHub/Vercel/Renderに入る | `.gitignore`, docs | `.next`, cache, test-results, db, env, logsをGit対象外へ明示 | `git status --short`, `git diff --check` | 生成物がGit対象外である |
| 2 | Maintenance Modeの生成停止に抜けがある | 停止中に提案書・PPT/PDF・Orchestratorが実行される | `backend/app/auth.py`, `backend/app/main.py`, `backend/app/routers/*` | Backendで503を返す共通ガードを生成系APIへ適用。環境変数を画面操作より優先 | pytest: 生成API 503、閲覧/health可、env時解除不可 | 停止中の新規生成がBackendで拒否される |
| 3 | `AppShell.tsx` が巨大 | 初期画面・管理者メニュー変更時の副作用 | `frontend/components/AppShell.tsx`, `frontend/components/app-shell/constants.ts` | まず安全な定数・型だけ分割し、挙動を変えない | `npm.cmd run typecheck`, `npm.cmd run build`, E2E | 既存UIが動き、AppShellの責務分離が始まっている |
| 4 | `repositories.py` が巨大 | DB変更時の影響範囲が広い | `backend/app/repositories.py` | RC1では認証/保守性に必要な最小変更のみ。大規模分割はPriority Bへ送る | pytest | 既存Repositoryの挙動を壊さない |
| 5 | `db.py` の起動時DDL/ALTER依存 | 本番DB変更の追跡・ロールバックが難しい | `backend/app/db.py`, `backend/alembic/*`, docs | Alembic baselineを追加。本番では `ALLOW_STARTUP_SCHEMA_MIGRATION=false` で危険な自動ALTERを停止可能にする | Alembic空DB適用テスト、pytest | 空DBへMigration適用でき、既存SQLiteは壊さない |
| 6 | 本番DB/バックアップ方針が未確定 | データ消失・復旧不能 | `docs/DATABASE_MIGRATION.md`, `docs/RELEASE.md`, `docs/OPERATIONS.md` | SQLite/PostgreSQLのバックアップ・Migration・復旧方針を明記 | docs確認 | Release手順にDBバックアップとMigrationが含まれる |
| 7 | Render本番環境変数の必須項目が運用依存 | 認証未設定・起動後degradedの見落とし | `docs/RELEASE.md`, `docs/OPERATIONS.md`, `/health/ready` | `APP_AUTH_SECRET`, 初期管理者, `DATABASE_URL` を必須確認へ明記 | `/health/ready` | readinessで不足が分かる |
| 8 | 本番CORSが広い | 想定外のVercel URLからアクセスされる | docs | RC1では設定手順を明記。コードの既存互換は維持 | docs確認 | 本番では固定URLに絞る運用が明文化される |
| 9 | Rate Limitがない | ブルートフォース、過剰生成、コスト増大 | `backend/app/rate_limit/*`, auth/生成/管理系router | インメモリ実装で開始し、Redis差し替え可能な境界を作る | pytest: 成功範囲、429、Retry-After、別ユーザー影響なし | 主要APIがBackendで429制御される |
| 10 | 認証トークン強化不足 | 無効ユーザーや権限変更後の古いトークンが使える | `backend/app/security.py`, `backend/app/auth.py`, `backend/app/db.py`, `repositories.py` | tokenに `issued_at`, `expires_at`, `auth_version` を含め、DB側と照合 | pytest: 無効ユーザー、auth_version不一致、期限 | 古い/無効なトークンが拒否される |
| 11 | 障害連絡・復旧目標が不足 | 事故時の判断遅延 | `docs/INCIDENT_RESPONSE.md` | Maintenance、DB、Rate Limit、Rollback判断を明記 | docs確認 | 重大障害時の初動が説明されている |
| 12 | Cloud Smoke Testの本番確認が手動依存 | Vercel/Renderの壊れに気づきにくい | `docs/RELEASE.md`, `docs/OPERATIONS.md` | Release前チェックへSmoke Testを明記 | docs確認 | Release手順にSmoke Testが含まれる |

## 追加Index/制約

RC1では監査でPriority A指定された新規Index不足はありません。無差別なIndex追加は行いません。  
追加した制約・列は以下のみです。

- `users.auth_version`: 権限変更・無効化・Pilot設定変更後に古いトークンを拒否するため。

## 完了判定

- Frontend: typecheck, check:unused, build, E2E
- Backend: compileall, pytest, pip check
- Migration: 空SQLite DBへ `alembic upgrade head`
- Dependency: npm audit/pip list/pip check結果を記録
- `git diff --check`

## RC1実施結果

2026-07-11時点の確認結果です。

- Backend Maintenance Mode: 主要な新規作成・生成系APIを503で停止し、閲覧・管理・解除系APIは維持しました。
- Rate Limit: login、生成/ダウンロード、Orchestrator、Learning、Prompt Experiment、External Intakeに429制御を追加しました。
- Auth/session: `APP_AUTH_SECRET`必須化、期限・inactive・pilot対象外・role/auth_version不一致をBackend側で拒否するようにしました。
- Migration: Alembic baselineを追加し、一時SQLite空DBへの `alembic upgrade head` を確認しました。
- Frontend error UX: Maintenance / Rate Limit を日本語で正しく分類し、PPTX失敗への誤分類を修正しました。
- AppShell整理: 定数類を `frontend/components/app-shell/constants.ts` に分離しました。
- Demo/estimated label: Dashboardに推定・デモ表示の注記を追加しました。
- Dependency audit: `docs/DEPENDENCY_AUDIT.md` にnpm/pip結果を記録しました。npm auditは既知アドバイザリありのため条件付きです。

確認結果:

- `npm.cmd run typecheck`: pass
- `npm.cmd run check:unused`: pass
- `npm.cmd run build`: pass
- `npm.cmd run test:e2e`: 13 passed
- `.\.venv\Scripts\python.exe -m compileall app tests`: pass
- `.\.venv\Scripts\python.exe -m pytest -q`: 92 passed
- `.\.venv\Scripts\python.exe -m pip check`: pass
- Empty DB migration: pass
- `git diff --check`: pass
- `npm.cmd audit --omit=dev`: findings remain; see `docs/DEPENDENCY_AUDIT.md`

RC1判定:

- ローカル検証範囲ではRC1として条件付きリリース可能です。
- 条件: npm auditの既知アドバイザリをRelease Noteに明記し、Next.js/Playwright更新時に再監査してください。
