# Version 17.0 Production Readiness Audit

監査日: 2026-07-11  
対象: AI営業秘書 / AI Workspace  
監査方針: 新機能追加・不具合修正は行わず、正式版 v1.0 公開可否を第三者目線で評価する。

## 1. 監査サマリー

現状は、社内試験導入から限定的な正式運用へ進めるための土台は揃っています。認証、権限、監査ログ、CRM、AI Workspace、PPT/PDF、Knowledge、Analytics、Pilot運用、CI/E2Eまで幅広く実装されています。

一方で、正式版 v1.0 として安心して公開するには、以下が主なリスクです。

- フロントエンドの `AppShell.tsx` と `globals.css` が大きく、保守性・表示崩れ時の調査性に課題があります。
- Backendの `repositories.py` と `db.py` に複数ドメインの責務が集中しています。
- SQLiteを維持しつつPostgreSQL対応準備は進んでいますが、正式なMigration運用は未完成です。
- 認証トークンが `localStorage` に保存されており、XSS発生時の影響が大きくなります。
- 生成・ダウンロード系APIのMaintenance Mode適用に抜けがあり、特に `/api/download-summary-pptx` は停止制御の確認・修正が必要です。
- Render本番環境変数、CORS、本番DB、バックアップ、障害対応基準の運用定義がリリース前に必要です。

結論: **△ 条件付き推奨**  
社内限定・管理者監視ありの運用開始は可能です。一般社内へ正式展開する前に、Priority A の項目を解消してください。

## 2. 実行確認結果

今回の監査で実行した確認は以下です。

| 確認項目 | 結果 |
| --- | --- |
| `npm.cmd run typecheck` | 成功 |
| `npm.cmd run check:unused` | 成功 |
| `npm.cmd run build` | 成功 |
| `npm.cmd run test:e2e` | 成功。Playwright 10件成功 |
| `python -m compileall app tests` | 成功 |
| `pytest -q` | 成功。86件成功 |
| `git diff --check` | 成功。ただしLF/CRLF変換警告あり |

補足:

- `git status --short` では多数の変更・未追跡ファイルが存在します。正式リリース前に、リリース対象差分を整理し、不要ファイルを除外してください。
- `backend/.pytest_cache/` へのアクセス警告が表示されました。テスト結果には影響していませんが、クリーンなリリース作業環境では削除または権限整理を推奨します。

## 3. Architecture監査

### 良い点

- `frontend` / `backend` / `docs` / `.github` が分離され、Vercel・Render・GitHub Actionsの役割が明確です。
- Backendは `routers`、`services`、`repositories`、`auth`、`db`、ドメイン別モジュールへ分割が進んでいます。
- Frontendも `components/dashboard`、`components/copilot`、`components/ai-workspace` など、後半の追加機能は分割されています。
- CIでBackend pytest、Frontend build、Playwright E2E、型チェックが実行される構成です。

### 懸念点

| ID | 指摘 | 影響 | 優先度 |
| --- | --- | --- | --- |
| ARCH-01 | `frontend/components/AppShell.tsx` が約6,733行あり、画面状態・API連携・管理者表示・生成導線が集中しています。 | 変更時の副作用、レビュー難度、再レンダリング増加 | Priority A |
| ARCH-02 | `frontend/app/globals.css` が約9,193行あり、UI変更時の影響範囲が読みづらい状態です。 | レスポンシブ崩れ、重複スタイル、保守性低下 | Priority B |
| ARCH-03 | `backend/app/repositories.py` が約1,404行あり、CRM、Pilot、Feedback、Audit、Readinessなど複数責務が混在しています。 | DB変更時の影響範囲が広い | Priority A |
| ARCH-04 | `backend/app/db.py` が約870行あり、テーブル作成、追加列、初期データ、DB種別吸収が集中しています。 | Migration移行時の難度上昇 | Priority A |
| ARCH-05 | `backend/app/services/pptx_service.py` が約1,889行あり、レイアウト・文章整形・スライド生成が密結合です。 | PPT改修時の回帰リスク | Priority B |
| ARCH-06 | `frontend/types/app.ts` が約959行あり、型定義が巨大化しています。 | 型変更時の見通し低下 | Priority C |
| ARCH-07 | `backend/app/prompts.py` が削除され、`backend/app/prompts/` と `proposal_prompts.py` が併存しています。 | import衝突は現状出ていませんが、命名衝突リスクは残ります | Priority B |
| ARCH-08 | 未追跡ファイルが多数あります。 | GitHub/Vercel/Renderへ意図しないファイルが入る可能性 | Priority A |

## 4. Frontend監査

### UX / UI

良い点:

- 一般ユーザー向け初期画面は、Daily Briefing、Sales Copilot、案件メール貼り付け、AI Workspace中心へ整理されています。
- 管理者機能は折りたたみ・メニュー化され、通常利用者への露出が抑えられています。
- Playwrightでログイン、Dashboard、案件入力、権限制御、Pilot Dashboardが確認されています。

改善点:

| ID | 指摘 | 影響 | 優先度 |
| --- | --- | --- | --- |
| FE-01 | 初期画面と管理者メニューの表示制御が `AppShell.tsx` に集中しています。 | UX変更時に広範囲へ影響 | Priority A |
| FE-02 | Dashboardの一部に「デモ目安」として固定値に近い表示が残っています。 | 実データと誤認される可能性 | Priority B |
| FE-03 | Loading、Toast、Error、Skeletonは存在しますが、全管理者パネルで統一されているとは言い切れません。 | エラー時の体験差 | Priority B |
| FE-04 | Playwrightは主要導線を確認していますが、360px/768px/1024px/1440pxの自動ビジュアル回帰は未整備です。 | 小画面崩れの検知不足 | Priority B |
| FE-05 | 管理者パネルの一部は開いたときだけ読み込む設計が進んでいますが、`AppShell.tsx` にimportが残るため初期バンドル影響の継続監視が必要です。 | 初期ロードの肥大化 | Priority B |

### レスポンシブ

- CSS上はスマホ1カラム、PC複数カラムを意識した構成です。
- ただし、9,000行超のCSSにより、同名・近似クラスの影響範囲確認が難しい状態です。
- 公式リリース前に、360px、768px、1024px、1440pxでのスクリーンショット確認を運用チェックに含めるべきです。

### アクセシビリティ

良い点:

- ボタン文言は日本語化され、主要操作は短く整理されています。
- Error Boundaryが導入され、画面全体のクラッシュを避ける設計があります。

不足:

- axe等による自動アクセシビリティテストは未導入です。
- モーダル、details、管理者メニュー、Copilot Quick Commandのキーボード操作はE2Eの網羅が限定的です。
- 状態表示が色だけに依存していないか、目視監査が必要です。

## 5. Backend監査

### Router / Service / Repository

良い点:

- `require_roles` によるAPI側権限チェックが広く導入されています。
- `observability.py` にリクエストID、ログ整形、機密情報マスクの考え方があります。
- `/health` が存在し、Render health checkの対象になっています。

責務混在:

| ID | 指摘 | 影響 | 優先度 |
| --- | --- | --- | --- |
| BE-01 | `repositories.py` に多ドメインのSQLが集中しています。 | 仕様変更時の影響範囲が広い | Priority A |
| BE-02 | `db.py` にDDL、追加列、seed、DB種別差分吸収が集中しています。 | Migration管理への移行が難しい | Priority A |
| BE-03 | `main.py` は主要生成APIを保持しており、router分割が一部未完了です。 | 生成系APIの共通制御漏れ | Priority B |
| BE-04 | `openai_service.py` が約934行あり、Prompt構成、Mock、整形、解析ロジックがまとまっています。 | AI品質調整時のテスト粒度が粗い | Priority B |

### Auth / Permission

良い点:

- `admin` / `manager` / `member` / `viewer` の権限モデルが導入されています。
- Backend API側でも多くの権限制御が行われています。
- Playwrightでmember/admin表示制御、pytestで権限制御が確認されています。

懸念:

- 認証トークンがFrontend `localStorage` に保存されています。
- ログイン試行回数制限、IPベース制限、生成APIのレート制限が明示的に見当たりません。
- `APP_ACCESS_PASSWORD` の簡易認証とユーザー管理認証が併存している場合、本番運用ルールを明確にする必要があります。

### Middleware / Logging / Config

良い点:

- Request ID、構造化ログ、CORS、health checkが導入されています。
- エラー表示は内部詳細を出しすぎない方向に整備されています。

懸念:

- `render.yaml` には `OPENAI_API_KEY` など一部しか明示されておらず、`APP_AUTH_SECRET`、`INITIAL_ADMIN_EMAIL`、`INITIAL_ADMIN_PASSWORD`、`DATABASE_URL` など正式運用に必要な環境変数はRender側での手動設定依存です。
- CORSはVercel全体を許可する正規表現を利用しており、正式ドメイン確定後は固定URLへ絞るべきです。

## 6. Database監査

### 良い点

- SQLiteとPostgreSQLの両対応を意識した `DATABASE_URL` 処理があります。
- 多くの主要テーブルに `CREATE INDEX IF NOT EXISTS` が追加されています。
- テーブル作成は既存DBを消さない `CREATE TABLE IF NOT EXISTS` で行われています。
- Knowledge、Analytics、Workspace、Review、Quality Gate、Integration、Pilotなどのデータ構造は分離されています。

### 懸念点

| ID | 指摘 | 影響 | 優先度 |
| --- | --- | --- | --- |
| DB-01 | Alembic等の正式Migrationではなく、起動時DDLと `_ensure_column` に依存しています。 | 本番DB変更の追跡・ロールバックが難しい | Priority A |
| DB-02 | `list_crm` 周辺で案件ごとにReview/Outcomeを追加取得するN+1傾向があります。 | データ増加時の遅延 | Priority B |
| DB-03 | `SELECT *` が複数箇所に残っています。 | 不要データ取得、将来の列追加影響 | Priority B |
| DB-04 | `pilot_issues.source_feedback_id` など一部にFKがありません。 | 参照整合性の低下 | Priority C |
| DB-05 | 日時がTEXT中心です。 | PostgreSQL移行後の日時演算・インデックス最適化が弱い | Priority B |
| DB-06 | JSON的なデータをTEXTに保存している列が複数あります。 | 集計・検索・検証が難しい | Priority C |
| DB-07 | `usage_logs`、`feedback_entries`、`audit_logs`、`proposal_histories`、`meeting_memos` には追加インデックス検討余地があります。 | 管理画面・集計の速度低下 | Priority B |

### PostgreSQL移行

PostgreSQLへ移行しやすい構造は準備されていますが、正式運用では以下が必要です。

- Alembic Migrationの導入
- 本番DBバックアップ手順
- Seed処理とMigration処理の分離
- SQLite専用SQLとPostgreSQL SQLの差分テスト
- 日時型、JSON型、FK、Indexの再設計

## 7. Security監査

### High

| ID | 指摘 | 理由 |
| --- | --- | --- |
| SEC-H-01 | 認証トークンが `localStorage` に保存されています。 | XSS発生時にトークン漏えいの影響が大きいです。HttpOnly Cookieまたは短寿命トークン+CSPの検討が必要です。 |
| SEC-H-02 | ログイン・生成・PPT/PDF系APIに明示的なRate Limitが見当たりません。 | ブルートフォース、過剰生成、コスト増大、DoSにつながります。 |
| SEC-H-03 | `/api/download-summary-pptx` に `ensure_not_maintenance_mode()` が見当たりません。 | Maintenance Mode中も要約PPT生成が可能になる恐れがあります。 |
| SEC-H-04 | 正式運用DBがSQLiteのままだと、Render環境で永続化・バックアップのリスクがあります。 | データ消失、復旧不能、監査証跡欠落につながります。 |

### Medium

| ID | 指摘 | 理由 |
| --- | --- | --- |
| SEC-M-01 | CORSが `https://.*.vercel.app` を許可しています。 | Preview利用には便利ですが、正式版では本番URLへ絞るべきです。 |
| SEC-M-02 | `APP_ACCESS_PASSWORD` の簡易認証が残る場合、ユーザー管理認証との運用境界が曖昧です。 | 想定外のログイン経路になる可能性があります。 |
| SEC-M-03 | Analytics eventはviewerもPOST可能です。 | ログ汚染・過剰イベント送信への対策が必要です。 |
| SEC-M-04 | CSP、X-Frame-Options等のセキュリティヘッダー運用が明確ではありません。 | XSS/クリックジャッキング耐性が弱くなります。 |
| SEC-M-05 | Request payload size limitが明確ではありません。 | 大量入力によるメモリ・処理負荷が懸念されます。 |
| SEC-M-06 | Audit Logはありますが、改ざん防止・保管期間・エクスポート方針が明文化不足です。 | 正式運用時の監査証跡として弱くなります。 |

### Low

| ID | 指摘 | 理由 |
| --- | --- | --- |
| SEC-L-01 | エラーにはrequest_idが付与されていますが、ユーザー向け文言と内部分類の統一を継続確認してください。 | サポート品質向上の余地があります。 |
| SEC-L-02 | `git diff --check` でLF/CRLF警告が出ています。 | セキュリティリスクではありませんが、CI差分の見通しに影響します。 |
| SEC-L-03 | 外部連携はDry Run中心で安全ですが、将来OAuth導入時のtoken保存禁止ルールを継続監査してください。 | 将来拡張時の漏えい予防です。 |

## 8. Performance監査

### 良い点

- Next.js production buildは成功し、First Load JSは約106KBでした。
- Playwright E2Eもローカルで安定して成功しました。
- 一部コンポーネントでdynamic import、memo、useMemoが導入されています。
- DBには主要検索向けのIndexが複数設定されています。

### 改善余地

| ID | 指摘 | 影響 | 優先度 |
| --- | --- | --- | --- |
| PERF-01 | `AppShell.tsx` が巨大で状態管理が集中しています。 | 不要再レンダリングの温床 | Priority A |
| PERF-02 | 管理者パネルの読み込み範囲をさらに分割できます。 | 初期ロード最適化 | Priority B |
| PERF-03 | PPT/PDF生成が同期処理中心です。 | 同時利用時にAPI workerを占有 | Priority B |
| PERF-04 | CRM・Analytics・Audit系一覧のページネーション/遅延読み込みを継続強化する必要があります。 | 大量データ時の遅延 | Priority B |
| PERF-05 | DBアクセスでN+1傾向がある箇所があります。 | 案件数増加時の応答悪化 | Priority B |
| PERF-06 | CSSが大きく、未使用CSSの分析が未実施です。 | 表示・保守への影響 | Priority C |

## 9. Test Coverage監査

### Frontend

確認済み:

- TypeScript型チェック
- 未使用import/未使用変数チェック
- Production build
- Playwright E2E 10件

未テスト・不足:

- React component unit test
- Accessibility automated test
- Visual regression test
- モバイル幅別E2E
- Error Boundaryの実クラッシュ時挙動
- 各管理者パネルの詳細操作
- PPT/PDFダウンロード前の品質ゲート実UIロックのE2E網羅

### Backend

確認済み:

- pytest 86件成功
- auth / permission
- health
- quality gate
- review
- pilot operations
- integrations
- knowledge
- learning
- orchestrator
- prompt experiments
- project lifecycle
- release management
- workspace conversations

未テスト・不足:

- PostgreSQL実DBでの統合テスト
- Alembic相当Migrationテスト
- Rate Limitテスト
- Maintenance Modeの全生成・全DLエンドポイント横断テスト
- 大量データ時のパフォーマンステスト
- XSS/CSP等のセキュリティヘッダーテスト
- OpenAI API制限時の実エラー分類テスト

### E2E / Smoke / CI

良い点:

- GitHub Actionsにbackend-test、frontend-build、frontend-e2e、lint-check、cloud-smokeがあります。
- cloud-smokeはworkflow_dispatchで安全に実行できる設計です。

不足:

- cloud-smokeは自動必須ジョブではありません。
- Vercel/Render本番URLを使った定期監視は未実装です。
- Lighthouse CIは未導入です。

## 10. Documentation監査

### 良い点

- `docs/SETUP.md`
- `docs/OPERATIONS.md`
- `docs/SECURITY.md`
- `docs/TROUBLESHOOTING.md`
- `docs/ARCHITECTURE.md`
- `docs/RELEASE.md`
- `docs/TESTING.md`
- `docs/PILOT_RUNBOOK.md`

上記が揃っており、社内試験導入の説明資料としては充実しています。

### 不足

| ID | 指摘 | 優先度 |
| --- | --- | --- |
| DOC-01 | 正式運用時のSLO/SLA、障害連絡先、復旧目標が未定義です。 | Priority A |
| DOC-02 | 本番DBバックアップ・リストア手順が運用レベルでまだ不足しています。 | Priority A |
| DOC-03 | Render本番環境変数の必須チェックリストをREADME/Runbookへ明示する必要があります。 | Priority A |
| DOC-04 | API一覧はありますが、OpenAPIベースの外部レビュー用仕様書は未整備です。 | Priority B |
| DOC-05 | データ保持期間、削除依頼、監査ログ保持期間の正式ルールが不足しています。 | Priority B |
| DOC-06 | Lighthouse、アクセシビリティ、Visual Regressionの確認手順が不足しています。 | Priority C |

## 11. Release Readiness採点

| 項目 | 点数 | コメント |
| --- | ---: | --- |
| Architecture | 72 | 機能分割は進んだが、巨大ファイルとRepository集中が残る |
| Security | 68 | 権限・監査ログはあるが、token保存、rate limit、CORS、DB運用が課題 |
| Performance | 70 | Buildは軽めだが、巨大AppShell、同期生成、DB N+1に改善余地 |
| Maintainability | 69 | テストは増えたが、責務集中が保守性を下げている |
| Usability | 78 | 初期導線は整理済み。管理者画面とデモ値の誤認防止が課題 |
| Test | 82 | pytest/E2E/CIが強い。a11y/visual/performance/PostgreSQLが不足 |
| Documentation | 84 | docsは充実。正式運用SLO/DB/環境変数チェックが不足 |
| Deployment | 72 | Vercel/Render構成はあるが、本番環境変数・DB・CORS確定が必要 |
| Operation | 76 | Pilot、Maintenance、Runbookあり。監視・アラート・バックアップが課題 |
| AI Quality | 73 | Knowledge/Learning/Prompt基盤あり。実データ評価と誤生成検知は継続課題 |
| 総合点 | 74 | 社内限定なら可。正式版は条件付き |

正式版リリース評価: **△ 条件付き推奨**

理由:

- 主要テストは成功しており、社内限定の利用開始には到達しています。
- ただし、正式版 v1.0 として広く公開するには、Security、DB運用、巨大ファイル解消、Maintenance制御、リリース差分整理が未完です。

## 12. 今後修正すべき項目

### Priority A

正式リリース前に対応してください。

1. リリース対象差分を整理し、未追跡ファイル・不要ファイルを除外する。
2. `/api/download-summary-pptx` を含む全生成・全DLエンドポイントでMaintenance Mode制御を横断確認する。
3. `AppShell.tsx` をさらに分割し、一般ユーザー初期画面、管理者メニュー、生成導線、Pilot運用を責務分離する。
4. `repositories.py` をドメイン別Repositoryへ分割する。
5. `db.py` のDDL・追加列・seed処理をMigration方針へ移行する。
6. 本番DBをPostgreSQLへ移行するか、SQLite継続時の永続化・バックアップ・復旧手順を確定する。
7. Render本番環境変数の必須項目を確定し、`APP_AUTH_SECRET`、`INITIAL_ADMIN_EMAIL`、`INITIAL_ADMIN_PASSWORD`、`DATABASE_URL` を運用チェックへ追加する。
8. 本番CORSを正式Vercel URL・独自ドメインへ限定する。
9. ログイン・生成・PPT/PDF APIにRate Limitを導入する。
10. 認証トークン保存方式を再検討し、少なくともCSPと短寿命トークン方針を明確化する。
11. 本番バックアップ・リストア手順、障害連絡先、復旧目標を文書化する。
12. Cloud Smoke Testを本番URLで実行し、Vercel/Render/health/ログイン/主要DLを確認する。

### Priority B

正式運用初期またはv1.1で対応してください。

1. `pptx_service.py` をレイアウト、データ整形、スライド別生成へ分割する。
2. `openai_service.py` をPrompt構築、Mock、AIレスポンス整形へ分割する。
3. CRM、Review、Outcome取得のN+1をJOINまたは集約クエリへ改善する。
4. `usage_logs`、`feedback_entries`、`audit_logs`、`proposal_histories` などに追加Indexを検討する。
5. PPT/PDF生成を非同期ジョブ化し、同時利用時の応答性を改善する。
6. Accessibility自動テストを導入する。
7. 主要画面のVisual Regression Testを導入する。
8. Dashboardのデモ目安値は、実測値に置き換えるか、より明確にデモ表示とする。
9. Audit Logの保持期間、エクスポート、改ざん防止方針を決める。
10. 管理者パネルをさらにlazy loadし、初期ロードを軽量化する。

### Priority C

継続改善として対応してください。

1. `frontend/types/app.ts` をドメイン別typeへ分割する。
2. `globals.css` を画面/コンポーネント単位で整理する。
3. Loading、Success、Error、Toast、SkeletonのUIパターンを完全統一する。
4. 管理者画面の検索・ページネーション・空状態表示を磨き込む。
5. READMEとdocsに構成図、ER図、API一覧の自動生成を追加する。
6. Lighthouse CIを導入する。
7. 外部連携OAuth導入前のSecurity Reviewテンプレートを追加する。
8. 監査ログ・Analytics・Knowledgeのデータ保持ルールを画面にも表示する。

## 13. 最終判断

**△ 条件付き推奨**

このアプリは、社内限定・少人数・管理者監視ありの正式運用候補としては十分な水準に近づいています。  
ただし、正式版 v1.0 として安定運用するには、Priority A の項目、特にMaintenance Mode制御、DB運用、認証/Rate Limit、巨大ファイル分割、リリース差分整理を完了してから公開することを推奨します。
