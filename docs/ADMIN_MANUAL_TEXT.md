# AI営業秘書 管理者向けマニュアル原稿

この文書は、将来 Word 化するための管理者向けテキスト原稿です。画像やスクリーンショットは含めません。

## 1. 管理者ログイン

管理者は、ログイン画面で「管理者ログイン」を選択します。

管理者ログインで確認すること:

- ユーザー管理
- Organization / Workspace 管理
- Analytics
- Audit Log
- Maintenance
- UAT
- Beautiful.ai 診断

一般利用者アカウントで管理者ログインはできません。

## 2. 詳細モード

詳細モードでは、通常画面では隠している運用・診断情報を確認できます。

確認できる情報:

- Frontend / Backend version
- Health
- Maintenance
- Beautiful.ai 状態
- OpenAI 状態
- Workspace
- Role

秘密情報、APIキー、DATABASE_URLは表示しない方針です。

## 3. User Management

ユーザー管理では、社内利用者の作成、権限、無効化を管理します。

主なロール:

- 管理者
- 組織管理者または管理者補助
- 一般利用者
- 閲覧者

注意:

- 不要になったユーザーは無効化してください。
- パスワードを平文で共有しないでください。

## 4. Organization

Organization は会社、部署、チームなどの単位です。

確認すること:

- 現在の Organization
- ユーザーが所属する Organization
- 他 Organization の情報が見えていないこと

## 5. Workspace

Workspace は Organization 内の作業場所です。

確認すること:

- 営業部、制作部、管理部などの Workspace
- 案件、Knowledge、Analytics が Workspace 単位で分離されていること

## 6. Analytics

Analytics では利用状況、提案書作成数、エラー、フィードバックなどを確認します。

見るべきポイント:

- 利用率
- 提案書作成数
- エラー件数
- フィードバック傾向
- 改善候補

## 7. Knowledge

Knowledge では、提案に活用するナレッジを管理します。

確認すること:

- 承認済みナレッジのみAI参照されること
- draft / rejected / archived が参照されないこと
- 機密情報が含まれていないこと

## 8. Prompt Studio

Prompt Studio では、Prompt version や Experiment を管理します。

注意:

- 本番中の Prompt 変更は影響範囲を確認してください。
- rollback 手順を残してください。

## 9. Learning

Learning Dashboard では、レビュー、品質ゲート、受注結果などから改善候補を確認します。

注意:

- 本文全文や顧客情報は保存しない方針です。
- 提案された改善は、人が確認してから採用してください。

## 10. Integrations

外部連携では、Gmail、Outlook、Slack、Teams など将来連携の準備状態を確認します。

現時点の注意:

- 実OAuth接続は行わない運用があります。
- token、refresh token、API key は保存しません。
- Dry Run は疑似データのみで行います。

## 11. Pilot

Pilot Dashboard では、社内試験導入の利用状況、フィードバック、Issue、終了判定を確認します。

見るべきポイント:

- 利用率
- 成功率
- 重大エラー数
- 未解決Issue数
- フィードバック平均

## 12. Audit Log

Audit Log では重要操作を確認します。

記録対象例:

- ログイン成功 / 失敗
- 権限不一致
- 品質ゲート完了
- 管理者バイパス
- Beautiful.ai 操作
- リリース公開

保存禁止:

- Password
- Token
- APIキー
- 顧客本文全文

## 13. UAT

UATモードでは、ブラウザ確認の進捗や結果を記録します。

注意:

- adminのみ利用可能です。
- member / viewer には表示しません。
- 結果はlocalStorage保存の場合があります。

## 14. Beautiful.ai 診断

確認すること:

- Enabled
- Configured
- Route
- Mock
- Maintenance
- Backend version

一般利用者には技術的な詳細を出しすぎない方針です。

## 15. Maintenance

重大障害時は Maintenance Mode を有効化できます。

停止対象:

- 新規提案書作成
- PPT/PDF新規生成
- Orchestrator新規実行

停止後も利用可能:

- ログイン
- CRM閲覧
- 履歴閲覧
- Pilot Dashboard
- Issue管理
- 監査ログ
- `/health`

## 16. Render

Backend は Render で稼働します。

確認すること:

- 最新 Deploy が Live
- commit が GitHub 最新と一致
- Logs に `Application startup complete`
- `/health`
- `/health/ready`

## 17. Vercel

Frontend は Vercel で配信します。

確認すること:

- 最新 Deployment が Ready
- Production deployment
- branch が main
- commit が GitHub 最新と一致
- Root Directory が `frontend`
- `NEXT_PUBLIC_API_URL` が Render Backend を指す

## 18. GitHub Actions

確認すること:

- Backend pytest
- Frontend build
- Typecheck
- Playwright E2E
- Smoke test

古い失敗履歴ではなく、最新 commit の結果を見てください。

## 19. Backup

SQLite利用時:

- `app.db` のバックアップを取得します。
- Render無料環境では永続化に注意してください。

PostgreSQL利用時:

- Render PostgreSQL、Supabase、Neon などのバックアップ機能を確認します。

## 20. Restore

復元前に確認すること:

- 復元対象
- 復元時刻
- 影響範囲
- 現在DBのバックアップ取得
- 作業者

## 21. 障害時対応

1. 影響範囲を確認
2. Maintenance Mode を検討
3. Render / Vercel / GitHub Actions を確認
4. Audit Log を確認
5. Issue を登録
6. 暫定対応を周知
7. 修正後に回帰確認

秘密情報や顧客本文全文を障害メモへ貼り付けないでください。
