# ProposalPilot 運用マニュアル

対象製品: ProposalPilot / AI営業秘書
運用責任者: 要入力
更新日: 要入力

## 1. 運用方針

ProposalPilotは、案件入力、AI提案書生成、提出前チェック、PowerPoint / PDF / Beautiful.ai出力、作成履歴、監査ログを扱います。

運用では以下を優先します。

- 顧客情報と秘密情報を保存しすぎない
- 管理者以外に管理機能を見せない
- Organization / Workspace分離を維持する
- AI生成結果は人間が確認してから社外提出する
- 障害時は原因追跡に必要なrequest_idと監査ログを確認する

## 2. 毎日の確認

- [ ] RenderがLive
- [ ] VercelがReady
- [ ] `/health` が正常
- [ ] `/health/ready` が正常
- [ ] 直近エラーが急増していない
- [ ] Beautiful.ai診断に異常がない
- [ ] ログイン失敗が異常に増えていない
- [ ] Quality Gate未完了のまま提出されていない
- [ ] 監査ログが記録されている

## 3. 週次確認

- [ ] 利用者数
- [ ] 作成案件数
- [ ] PPTX / PDF / Beautiful.ai生成件数
- [ ] Beautiful.ai成功 / 失敗
- [ ] 直近の権限エラー
- [ ] 無効ユーザーのログイン試行
- [ ] Organization / Workspaceの不整合
- [ ] バックアップ取得状況
- [ ] サポート問い合わせ状況

## 4. 月次確認

- [ ] 管理者アカウント棚卸し
- [ ] 退職者・異動者の無効化
- [ ] Workspace権限の見直し
- [ ] 監査ログの保存方針確認
- [ ] 利用規約・プライバシーポリシーの更新要否
- [ ] 料金表の更新要否
- [ ] ブランド資産の更新要否

## 5. ユーザー管理

### 新規ユーザー作成

1. 管理者でログインする
2. ユーザー管理を開く
3. 氏名、メールアドレス、Role、Organization、Workspaceを入力する
4. 初期Passwordを設定する
5. 必要に応じて次回ログイン時のPassword変更を必須にする
6. 作成後、対象ユーザーへログイン方法を案内する

### 無効化

1. 対象ユーザーを確認する
2. 所属Organization / Workspaceを確認する
3. 有効状態を無効へ変更する
4. 監査ログに記録されていることを確認する

最後の有効adminは無効化しないでください。

## 6. Password再設定

1. 管理者でログインする
2. ユーザー管理を開く
3. 対象ユーザーを選択する
4. 仮Passwordを発行する
5. 次回ログイン時のPassword変更を必須にする
6. 仮Passwordは安全な方法で本人へ伝える

Passwordをチャット、公開チャンネル、チケット本文へ残さないでください。

## 7. Beautiful.ai運用

確認する項目:

- API Enabled
- API Mode
- Resolved Endpoint
- Workspace ID
- Theme ID
- 最後のHTTP Status
- 最後のError Type
- 最後のResponse Text
- 最後の実行日時

障害時の確認順:

1. 管理画面のBeautiful.ai診断
2. Renderログ
3. Resolved Endpoint
4. API Mode
5. Workspace ID / Theme ID
6. 直近20件の通信履歴
7. 利用者画面のrequest_id

APIキーの値は確認・共有しないでください。

## 8. Maintenance Mode

重大障害時は、管理者がMaintenance Modeを有効化できます。

停止対象:

- 新規提案書作成
- PPTX / PDF新規生成
- Orchestrator新規実行

継続利用可能:

- ログイン
- CRM閲覧
- 履歴閲覧
- 管理画面
- 監査ログ
- `/health`

停止理由、実行者、時刻を監査ログで確認してください。

## 9. 障害対応

1. 影響範囲を確認する
2. Maintenance Modeの要否を判断する
3. request_idを控える
4. Render / Vercel / GitHub Actionsを確認する
5. 監査ログを確認する
6. 暫定回避策を利用者へ案内する
7. 修正後、再発防止策を記録する

## 10. データ取り扱い

保存しないもの:

- APIキー
- Password
- Token
- Authorizationヘッダー
- 顧客本文全文
- 個人情報を含む不要なログ

保存する場合も最小限にするもの:

- 操作ログ
- エラー概要
- request_id
- 集計値
- 生成結果のメタ情報

## 11. バックアップ

バックアップ方針:

- 本番DBの自動削除は行わない
- 復旧前にバックアップを追加取得する
- 復旧後はHealth、Migration、主要動線を確認する
- SQLiteとPostgreSQLで手順を分けて管理する

詳細は `docs/BACKUP_RESTORE.md` を確認してください。
