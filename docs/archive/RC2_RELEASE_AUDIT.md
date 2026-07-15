# Version 21.0 RC2 Release Audit

実施日: 2026-07-13
対象: AI営業秘書 / AI Workspace / Version 20.3 時点
目的: Version 20 までの既存機能を、正式版 v1.0 Release Candidate として公開可能か監査する。

## 結論

リリース可否: **△ 条件付き推奨**

総合完成度: **87 / 100**

今回のローカル自動確認では重大な失敗は検出されませんでした。社内限定の正式版 v1.0 RC2 としては公開候補にできます。ただし、正式公開前には人間による UAT、Vercel / Render / Beautiful.ai の本番疎通、バックアップ・リストア手順の確認を必須ゲートにしてください。

## スコア

| 項目 | 点数 | 評価 |
| --- | ---: | --- |
| Architecture | 78 | 機能分割は進んでいるが、AppShell.tsx と globals.css に責務が残りすぎている。 |
| Security | 88 | 権限、Workspace分離、秘密情報非表示は概ね整備済み。最終UATでIDORと管理者APIを再確認する。 |
| Performance | 82 | 初期表示の管理機能抑制、E2Eは整備済み。巨大CSS/Componentが残り、Bundle最適化余地あり。 |
| Maintainability | 76 | Backend Routerは小さめだが、db.py / repositories.py / pptx_service.py が大きい。 |
| Usability | 88 | UATモード、Sales Copilot、初期画面整理がある。実ユーザー確認が残る。 |
| Test | 91 | pytest / Playwright / typecheck / build が整備済み。クラウドSmokeは人間確認が必要。 |
| Documentation | 90 | Runbook、Security、UAT、Beautiful.ai、Optimization等の文書は揃っている。RC2文書で判断基準を補完。 |
| Deployment | 84 | Vercel Hobby制約や Beautiful.ai 疎通対応済み。実デプロイの同期確認は必須。 |
| Operation | 88 | Pilot、Maintenance、Issue、Incident、Backup文書あり。運用リハーサルが未完。 |
| AI Quality | 85 | Presentation Review / Optimization / Learning は整備済み。実案件での品質評価はUAT後に判断。 |

## 監査範囲

- Frontend: Dashboard、Sales Copilot、AI Workspace、UAT、Beautiful.ai、Presentation Review、Optimization、Admin panels
- Backend: Routers、Services、Repositories、Auth、Permission、Organization / Workspace、Maintenance、Rate Limit、Audit Log
- Database: Alembic migration、SQLite / PostgreSQL移行方針、Organization / Workspace列、Audit / Analytics / Knowledge / Review / Optimization
- Operations: GitHub Actions、Vercel、Render、Health、Backup、Incident、Release、Runbook
- Security: Role、IDOR、XSS、CSRF、CORS、秘密情報、監査ログ、外部連携、Beautiful.ai / OpenAI

## Phase 1: コード監査結果

### Frontend

確認結果:

- `frontend/components/AppShell.tsx` が約7,000行超で、画面組み立て、状態管理、業務ロジック、管理者表示がまだ混在している。
- `frontend/app/globals.css` が約10,000行で、機能ごとのCSS分離が不足している。
- `components/dashboard/`、`components/copilot/`、`components/ai-workspace/` などの分割は進んでいる。
- `dangerouslySetInnerHTML`、`innerHTML`、`eval`、`new Function`、`document.write` はアプリ本体では検出されなかった。
- `console.log` はE2Eテスト補助と logger 実装に限定されている。
- `TODO` 検出は AppShell 内の文字列 `"TODO"` で、未実装コメントではなく議事録抽出キーワード。

主な改善余地:

- AppShellのさらなる責務分離
- CSSの機能単位分割
- 管理者パネルの動的読み込み徹底
- UAT結果コメントの入力注意文はあるが、実ユーザーが機密情報を入れない運用教育が必要

### Backend

確認結果:

- Routerの最大規模は `logs.py` 約175行、`proposal_optimization.py` 約170行で、Router巨大化は限定的。
- `repositories.py`、`db.py`、`pptx_service.py` が大きく、正式運用後の変更リスクが高い。
- `app.prompts` はパッケージとして利用されており、過去に問題になった `schemas.py` / `schemas/` 型の衝突は現状の監査対象では再発していない。
- Alembic版ファイルは存在し、Version 20系の migration が整理されている。
- `OPENAI_API_KEY`、`APP_AUTH_SECRET`、`DATABASE_URL`、`BEAUTIFUL_AI_API_KEY` はBackend config側で読み込み。Frontendに値そのものを出す箇所は見当たらない。

主な改善余地:

- `db.py` の初期化、列追加、seed処理をさらに小さなモジュールへ分離
- `repositories.py` をドメイン別Repositoryへ段階分割
- `pptx_service.py` をテンプレート、描画、出力、検証へ分離
- PostgreSQL本番移行前にAlembic運用を完全化

### Database

確認結果:

- Alembic migration:
  - `20260711_1701_initial_schema.py`
  - `20260713_1820_workspace_isolation_acceptance.py`
  - `20260713_1900_presentation_review_loop.py`
  - `20260713_1910_presentation_review_acceptance.py`
  - `20260713_2000_proposal_optimization.py`
  - `20260713_2010_proposal_optimization_acceptance.py`
- Organization / Workspace分離用の方針とテストは存在する。
- SQLite維持とPostgreSQL移行方針は文書化済み。

リスク:

- Index設計は本番データ量での実測が未完。
- FK制約は段階導入のため、Repository / Service側のスコープチェックに依存している箇所がある可能性。
- 既存SQLiteからPostgreSQLへの本番移行リハーサルは未確認。

## Phase 2: リファクタリング判断

RC2では、正式候補直前のため巨大ファイルの大規模分割は実施しませんでした。機能仕様を変えずに分割できる余地は大きいものの、`AppShell.tsx`、`globals.css`、`pptx_service.py`、`repositories.py`、`db.py` は影響範囲が広く、RC2での大きな変更はリリース安定性を下げるためです。

Version 22で優先的に分割すべき巨大ファイル:

| ファイル | 状態 | 推奨対応 |
| --- | --- | --- |
| `frontend/components/AppShell.tsx` | 約7,000行超 | feature shell、admin shell、proposal flow、UAT、Beautiful.ai制御へ分割 |
| `frontend/app/globals.css` | 約10,000行 | dashboard / admin / workspace / uat / forms などへCSS分割 |
| `backend/app/services/pptx_service.py` | 約1,800行超 | slide builder、template、export、validationへ分割 |
| `backend/app/repositories.py` | 約1,600行超 | audit / pilot / release / CRM / settings別Repositoryへ分割 |
| `backend/app/db.py` | 約1,400行超 | engine、migration helper、seed、schema compatibilityへ分割 |

## Phase 3: Performance監査

確認結果:

- Sales Copilot、Dashboard、AI Workspaceは一部 `memo` / `useMemo` / dynamic loading を利用。
- 管理者向け機能は初期表示から隠す設計になっている。
- Playwright E2Eは広範囲を確認するため実行時間が長い。

改善余地:

- AppShell状態の細分化による再レンダリング削減
- Admin panelsのさらなる遅延読み込み
- 大量ログ・Analytics・Knowledge一覧のAPIページネーション確認
- CSS肥大化による初期レンダリングコストの削減
- Lighthouse実測は未実施のため、正式前にVercel Previewで測定する

## Phase 4: Security監査

### High

現時点でコード監査から直ちに公開停止と判断するHighは未検出。
ただし以下は本番前に人間確認が必須:

- Organization跨ぎ・Workspace跨ぎの参照不可テストを本番相当データで確認
- admin / manager / member / viewer の管理者APIアクセス拒否
- Beautiful.ai操作がWorkspaceスコープから外れないこと
- Maintenance中に停止対象だけが止まり、閲覧系は残ること

### Medium

- Repository / Service側のスコープチェックに依存する箇所が残る可能性。DB FK / index / unique制約の強化が今後必要。
- UATコメントやフィードバック欄にユーザーが機密情報を入力するリスク。UI注意と運用教育で軽減済みだが完全防止ではない。
- CORS / CSRF はBackend設定とVercel / Render環境変数の最終確認が必要。
- Rate Limitの本番閾値が業務量に対して適切か未検証。

### Low

- Frontend文言内に環境変数名は表示されるが、値そのものは表示しない設計。
- E2E用のconsole出力はテスト時のみで、本番情報漏洩リスクは低い。
- Dry Run / Demo表示は存在するが、外部連携は実OAuthなしの準備機能として明示されている。

## Phase 5: Release Readiness

整備済み:

- GitHub Actions: Backend pytest、Frontend build / typecheck 系
- Vercel / Renderの基本文書
- Beautiful.ai確認文書
- UATチェックリスト
- Security / Operations / Incident / Backup / Release / Troubleshooting docs
- Maintenance Mode、Pilot、Issue、Audit Log、Health確認

公開前に必要:

- GitHub Actions最新成功確認
- Vercel最新Deploymentが対象commitであること
- Render最新Deploymentが対象commitであること
- `/health` の `db_connected`、`auth_configured`、`ai_api`、`pptx`、`pdf` の確認
- Beautiful.ai `/api/beautiful-ai/status` とFrontend Status Cardの一致確認
- SQLite運用なら `app.db` のバックアップ取得
- PostgreSQL運用なら接続先、バックアップ、リストア手順確認
- `APP_AUTH_SECRET`、`INITIAL_ADMIN_EMAIL`、`INITIAL_ADMIN_PASSWORD`、`OPENAI_API_KEY`、`BEAUTIFUL_AI_API_KEY` 等の環境変数確認

## Phase 6: Acceptance評価

| 領域 | 評価 | コメント |
| --- | --- | --- |
| UAT | 条件付き合格 | UATモードとチェックリストはある。実ブラウザで人間確認が必要。 |
| Presentation Review | 合格候補 | DB/API/UI/テストが整備済み。Beautiful.ai Revision実連携は本番確認が必要。 |
| Optimization | 合格候補 | Evidence governanceまで整備済み。実案件での効果検証は運用後。 |
| Beautiful.ai | 条件付き合格 | 表示・Status・Mock/Enabled条件は対応済み。本番APIキーでの実生成確認が必要。 |
| Workspace | 合格候補 | Organization / Workspace分離対応済み。追加の実データUATを推奨。 |
| Role | 合格候補 | admin/member/viewer/manager確認済み。管理者APIの本番Smokeが必要。 |
| Organization | 合格候補 | migration/docs/testsあり。既存データ移行後の確認が必要。 |

## Release Blocker

コード監査時点で、ローカルリリースを即時停止する確定Blockerは未検出。

ただし、以下が未完了の場合は正式版公開を止めること:

1. GitHub Actionsが最新commitで失敗している。
2. Vercelが最新Frontendを配信していない。
3. Render `/health` が異常。
4. Beautiful.ai Statusが404/500またはFrontendとBackend version mismatch。
5. UAT重大項目で `×` が1件以上ある。
6. Backup / Restore手順が確認されていない。
7. Organization / Workspace跨ぎアクセスが再現する。

## RC2ローカル確認結果

| 確認 | 結果 | メモ |
| --- | --- | --- |
| `npm.cmd run typecheck` | 成功 | TypeScript型チェック成功 |
| `npm.cmd run check:unused` | 成功 | 未使用ローカル検出用の補助チェック成功 |
| `npm.cmd run build` | 成功 | Next.js production build成功 |
| `npm.cmd run test:e2e` | 成功 | Playwright 29件成功 |
| `python -m compileall backend/app backend/tests` | 成功 | Backend app/tests 構文チェック成功 |
| `pytest -q` | 成功 | pytest 139件成功 |
| `pip check` | 成功 | Python依存関係の破損なし |
| `git diff --check` | 成功 | 空白エラーなし。LF→CRLF警告のみ |

クラウド確認はこのローカル環境からは未実施です。GitHub Actions、Vercel、Render、Beautiful.ai実生成は公開前に人間が確認してください。

## Known Issues

- AppShell / CSS / Backend基盤ファイルが大きく、今後の変更コストが高い。
- UATのMigration VersionはBackendから取得できない場合があり、未取得表示になることがある。
- E2Eは網羅性がある一方、実行時間が長い。
- 外部連携はDry Run / Connector readiness段階であり、実OAuth接続ではない。
- Learning / Optimizationの効果値は推定であり、正式な効果測定は運用データ蓄積後。
- `git status` に過去作業分の変更が多いため、リリース前に意図した差分だけを確認してcommitする必要がある。

## Priority A

正式版 v1.0 公開前に必ず実施:

1. `docs/UAT_CHECKLIST.md` に沿ってadmin / member / viewerでブラウザUATを完了する。
2. Vercel / Render が同じGit commitを配信していることを確認する。
3. Render `/health`、Beautiful.ai Status Card、Frontend Build情報の一致を確認する。
4. Organization / Workspace分離を本番相当の複数組織データで確認する。
5. Backup / Restore手順を1回リハーサルする。
6. 本番環境変数に秘密情報が正しく設定され、画面やログへ値が出ないことを確認する。
7. UAT重大不具合が0件であることを確認する。

## Priority B

正式版公開直後またはVersion 22で実施:

1. `AppShell.tsx` を画面責務別に分割する。
2. `globals.css` を機能単位へ分割する。
3. `pptx_service.py`、`repositories.py`、`db.py` を段階分割する。
4. Alembic migration運用を完全化し、起動時の互換列追加を縮小する。
5. 本番データ量を想定したDB index / query / N+1確認を行う。
6. Lighthouse / Web Vitals測定をVercel Previewで実施する。
7. E2EをSmoke / Full / Adminに分け、CI時間を短縮する。

## Priority C

中期改善:

1. Visual regression testを追加する。
2. Storybook相当のUIカタログを作る。
3. Audit Log / Analyticsの長期保管・アーカイブ方針を自動化する。
4. Production PostgreSQLへの移行リハーサルを定期化する。
5. Optimization / Learningの実効果を月次で評価する。

## 公開前チェックリスト

- [ ] GitHub Actions 最新commit成功
- [ ] `npm.cmd run typecheck` 成功
- [ ] `npm.cmd run build` 成功
- [ ] `npm.cmd run test:e2e` 成功
- [ ] `python -m compileall backend/app backend/tests` 成功
- [ ] `pytest` 成功
- [ ] `pip check` 成功
- [ ] `git diff --check` 成功
- [ ] Vercel Ready
- [ ] Render Live
- [ ] Render `/health` 正常
- [ ] Beautiful.ai status 正常
- [ ] UAT重大不具合0件
- [ ] Backup取得済み
- [ ] Restore手順確認済み
- [ ] admin/member/viewer/manager権限確認済み
- [ ] Organization / Workspace分離確認済み
- [ ] Maintenance Mode停止範囲確認済み
- [ ] 本番環境変数確認済み

## Version 22でやるべきこと

実装はRC2では行わない。次版候補:

1. 巨大ファイル分割スプリント
2. PostgreSQL production migration rehearsal
3. CI高速化とE2E層分離
4. Lighthouse / Accessibility自動測定
5. Production observability強化
6. UAT結果に基づく不具合修正
7. Backup / Restore自動確認
8. Organization / WorkspaceスコープのDB制約強化
