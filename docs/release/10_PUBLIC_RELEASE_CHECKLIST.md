# ProposalPilot 公開リリースチェックリスト

対象製品: ProposalPilot / AI営業秘書
公開日: 要入力
公開責任者: 要入力

## 1. リリース判定サマリー

| 項目 | 結果 |
| --- | --- |
| 公開URL | 要入力 |
| Backend URL | 要入力 |
| GitHub commit | 要入力 |
| Vercel deployment | 要入力 |
| Render deployment | 要入力 |
| 公開判定 | 要入力 |
| 残課題 | 要入力 |

## 2. 公開前

- [ ] GitHub Actions成功
- [ ] Vercel Ready
- [ ] Render Live
- [ ] `/health` 正常
- [ ] `/health/ready` 正常
- [ ] DB Migration Ready
- [ ] Backup取得済み
- [ ] Rollback手順確認済み
- [ ] Maintenance Mode解除
- [ ] 管理者ログイン確認
- [ ] memberログイン確認
- [ ] viewer権限確認

## 3. Web公開

- [ ] 独自ドメイン反映
- [ ] SSL有効
- [ ] favicon表示
- [ ] OGP表示
- [ ] `robots.txt` 確認
- [ ] `sitemap.xml` 確認
- [ ] Google Analytics計測
- [ ] Google Search Console登録
- [ ] CTAリンク確認
- [ ] 資料ダウンロード導線確認

## 4. アプリ確認

- [ ] 7ステップUI
- [ ] 案件入力
- [ ] AI生成
- [ ] 内容確認
- [ ] 提出前チェック
- [ ] 要約PowerPoint
- [ ] 詳細PowerPoint
- [ ] 見積PDF
- [ ] Beautiful.ai
- [ ] AIレビューと改善
- [ ] 作成履歴
- [ ] 監査ログ
- [ ] Logout

## 5. 管理者確認

- [ ] ユーザー管理
- [ ] Role変更
- [ ] Password再設定
- [ ] 無効ユーザー拒否
- [ ] Organization / Workspace管理
- [ ] Analytics
- [ ] Audit Log
- [ ] Beautiful.ai診断
- [ ] Maintenance Mode
- [ ] UATモード

## 6. 法務・商用

- [ ] 利用規約
- [ ] プライバシーポリシー
- [ ] 特定商取引法に基づく表記
- [ ] 料金表
- [ ] サポートポリシー
- [ ] 問い合わせ導線
- [ ] 会社情報

## 7. 公開後1時間

- [ ] 本番URLアクセス
- [ ] 主要ページ表示
- [ ] ログイン
- [ ] 主要APIエラーなし
- [ ] Renderログに重大エラーなし
- [ ] Vercelログに重大エラーなし
- [ ] Google Analyticsリアルタイム計測
- [ ] 問い合わせ導線確認

## 8. 公開後24時間

- [ ] ログイン失敗急増なし
- [ ] 500エラー急増なし
- [ ] Beautiful.ai失敗急増なし
- [ ] PPTX / PDF失敗急増なし
- [ ] 権限エラー異常なし
- [ ] サポート問い合わせ確認
- [ ] Search Console登録状況確認

## 9. Rollback基準

以下に該当する場合は、公開停止またはrollbackを検討します。

- 管理者・利用者ともにログイン不可
- DB接続不能
- Organization / Workspace越境の疑い
- PasswordやAPIキーの漏えい疑い
- 主要出力が広範囲で利用不可
- Beautiful.ai障害により業務影響が大きい
- 監査ログが記録されない

## 10. Rollback手順

1. 原因commitを特定する
2. `git revert <commit>` を実行する
3. `git push origin main` を実行する
4. GitHub Actionsを確認する
5. Vercel / Renderの再デプロイを確認する
6. `/health` と主要動線を確認する
7. 利用者へ復旧状況を案内する

force pushは使用しません。

## 11. 公開告知テンプレート

件名: ProposalPilot / AI営業秘書 公開のお知らせ

本文:

本日、ProposalPilot / AI営業秘書を公開しました。

公開URL: 要入力
対象利用者: 要入力
主な機能: 案件入力、AI提案書生成、提出前チェック、PowerPoint / PDF出力、Beautiful.ai連携、作成履歴、監査ログ
問い合わせ先: 要入力

利用前に、顧客の機密情報、Password、APIキー、Tokenを入力しないようご注意ください。

## 12. 最終承認

| 役割 | 氏名 | 判定 | 日時 |
| --- | --- | --- | --- |
| リリース責任者 | 要入力 | 要入力 | 要入力 |
| 技術責任者 | 要入力 | 要入力 | 要入力 |
| 運用責任者 | 要入力 | 要入力 | 要入力 |
| 営業責任者 | 要入力 | 要入力 | 要入力 |
