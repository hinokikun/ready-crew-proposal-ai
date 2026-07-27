# Version 71 Release Readiness

Version 71 Training Submission Release Candidateの提出前判定レポートです。Version70までの機能を維持し、研修提出に必要な実測データ記録、デモデータ分離、提出用Markdown、発表原稿、利用者マニュアル、管理者手順を整備しています。

## 判定

READY WITH WARNINGS

## 根拠

- 実測データの登録、短縮時間、短縮率、CSV、研修提出Markdown、発表用サマリーの導線を確認できる状態です。
- デモデータには `is_demo` を付与し、通常のKPI、統計、CSV、研修提出レポート、発表用サマリーから除外する設計です。
- migrationは列追加のみで、既存データを削除しません。
- クラウド本番環境での実ログイン、Vercel/Renderの再デプロイ、Beautiful.ai実生成は人の確認が必要です。

## テスト結果

| 項目 | 結果 | 備考 |
| --- | --- | --- |
| Frontend typecheck | PASS | `npm.cmd run typecheck` |
| Frontend check:unused | PASS | `npm.cmd run check:unused` |
| Frontend build | PASS | `npm.cmd run build` |
| Backend compileall | PASS | `python -m compileall app tests` |
| 関連pytest | PASS | 業務改善レポート、デモ分離、migration |
| 全pytest | PASS | Backend全体pytest |
| Alembic migration確認 | PASS | 空DB upgradeで最新revision `20260722_7100` まで確認 |
| git diff --check | PASS | 空白エラーなし |

## 未解決の問題

- 本番Render/Vercelでの再デプロイ確認は未実施です。
- Beautiful.aiの実生成は外部APIを利用するため、本番反映後に人が確認してください。
- SQLiteを一時領域で利用している場合、再デプロイ時にデータが消える可能性があります。

## 本番反映前に必要な作業

1. Git差分を確認します。
2. 秘密情報が差分に含まれていないことを確認します。
3. 本番DBをバックアップします。
4. migrationをステージングまたは検証DBで適用します。
5. RenderとVercelの環境変数名を確認します。
6. デプロイ後、ログイン、提案生成、PPTX、PDF、Beautiful.ai、業務改善レポート、CSV、研修提出Markdownを確認します。

## migration適用手順

1. `20260722_2500_training_metrics.py`
2. `20260722_5000_proposal_agent_memory.py`
3. `20260722_7100_training_submission_rc.py`

確認項目:

- 空DBから最新までupgradeできること。
- 既存DBへupgradeしても既存データが残ること。
- `business_improvement_reports` に `ai_input_minutes`、`ai_wait_minutes`、`is_demo` があること。
- `proposal_histories` に `is_demo` があること。
- `/health/ready` でDBとmigrationが正常であること。

## 環境変数の確認事項

- `APP_AUTH_SECRET`
- `INITIAL_ADMIN_EMAIL`
- `INITIAL_ADMIN_PASSWORD`
- `OPENAI_API_KEY`
- `BEAUTIFUL_AI_API_KEY`
- `BEAUTIFUL_AI_ENABLED`
- `BEAUTIFUL_AI_API_MODE`
- `DATABASE_URL`
- `NEXT_PUBLIC_API_BASE_URL`

実値はこの文書に記載しません。

## ロールバック方法

重大障害が出た場合は、該当commitを `git revert` で戻します。`reset --hard` やforce pushは使いません。DB migrationは列追加のみのため、原則としてデータ削除を伴うdowngradeは行いません。

## 既知の制限

- デモデータは研修提出用の実測値ではありません。
- 測定回数が3回未満の場合は、提出レポート内で注意表示します。
- 平均短縮率が50％未満の場合は、提出を止めずに事実として注意表示します。
- 本番でSQLiteを利用する場合は、永続化方式を別途確認してください。

## 提出に使用できる状態か

READY WITH WARNINGS。実測データを人が登録し、提出前チェックリストを完了すれば研修提出に使用できます。

## 本番公開できる状態か

READY WITH WARNINGS。本番公開前に、クラウド環境でのmigration、ログイン、外部API、出力機能を人が確認してください。
