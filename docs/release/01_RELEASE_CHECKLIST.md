# ProposalPilot 公開前チェックリスト

対象製品: ProposalPilot / AI営業秘書
リリース種別: Version 1.0 正式公開
リリース責任者: 要入力
確認日: 要入力

## 1. 公開判定

| 項目 | 判定 | 確認者 | メモ |
| --- | --- | --- | --- |
| GitHub Actionsが成功している | 要入力 | 要入力 | 要入力 |
| Vercel ProductionがReady | 要入力 | 要入力 | 要入力 |
| RenderがLive | 要入力 | 要入力 | 要入力 |
| `/health` が正常 | 要入力 | 要入力 | 要入力 |
| `/health/ready` が正常 | 要入力 | 要入力 | 要入力 |
| MigrationがReady | 要入力 | 要入力 | 要入力 |
| Maintenance Modeが解除済み | 要入力 | 要入力 | 要入力 |
| 管理者ログイン確認済み | 要入力 | 要入力 | 要入力 |
| memberログイン確認済み | 要入力 | 要入力 | 要入力 |
| viewer権限確認済み | 要入力 | 要入力 | 要入力 |
| Organization / Workspace分離確認済み | 要入力 | 要入力 | 要入力 |

## 2. GitHub

- [ ] `main` ブランチが公開対象である
- [ ] 最新commitがGitHubへpush済みである
- [ ] 最新commitとGitHub Actionsの対象commitが一致している
- [ ] Backend pytestが成功している
- [ ] Frontend buildが成功している
- [ ] Playwright E2Eが成功している
- [ ] 秘密情報がcommitに含まれていない
- [ ] `.env`、DB実体、生成PPTX、生成PDF、`node_modules`、`.next`、テスト結果ディレクトリが含まれていない
- [ ] Release NotesとCHANGELOGが更新済みである

## 3. Vercel

- [ ] Production DeploymentがReady
- [ ] Root Directoryが `frontend`
- [ ] `NEXT_PUBLIC_API_URL` が本番Render Backend URLを指している
- [ ] Build Logsにエラーがない
- [ ] 本番URLをCtrl + F5で再読み込みして最新表示を確認した
- [ ] Frontend Build Versionが最新commitと一致している
- [ ] Serverless Function上限エラーがない
- [ ] 独自ドメインのSSLが有効

## 4. Render

- [ ] 最新DeployがLive
- [ ] RenderのcommitがGitHub最新commitと一致している
- [ ] Application startup completeが出ている
- [ ] `/health` が正常
- [ ] `/health/ready` が正常
- [ ] `db_connected` が正常
- [ ] `migration_ready` が正常
- [ ] `maintenance_mode` が意図した状態
- [ ] Beautiful.ai resolved endpointが確認できる

## 5. アプリ主要動線

- [ ] 管理者ログイン
- [ ] memberログイン
- [ ] viewerログイン
- [ ] 案件入力
- [ ] AI提案書生成
- [ ] 提出前チェック
- [ ] 要約PowerPoint生成
- [ ] 詳細PowerPoint生成
- [ ] 見積PDF生成
- [ ] Beautiful.ai生成
- [ ] Presentation Review
- [ ] Proposal Optimization
- [ ] 作成履歴
- [ ] 監査ログ
- [ ] Logout

## 6. 公開Web設定

- [ ] 独自ドメイン設定
- [ ] favicon設定
- [ ] OGP画像設定
- [ ] OGP title / description設定
- [ ] `robots.txt` 設定
- [ ] `sitemap.xml` 設定
- [ ] Google Analytics設定
- [ ] Google Search Console登録
- [ ] LPのCTAリンク確認
- [ ] 製品資料ダウンロード導線確認

## 7. 法務・商用文書

- [ ] 利用規約が公開可能
- [ ] プライバシーポリシーが公開可能
- [ ] 特定商取引法に基づく表記が公開可能
- [ ] 料金表が公開可能
- [ ] サポートポリシーが公開可能
- [ ] 会社名、住所、連絡先、責任者名の「要入力」がすべて埋まっている
- [ ] 外部サービス利用の説明が正しい
- [ ] AI生成物は人間確認が必要である旨が明記されている

## 8. ブランド資産

- [ ] ロゴ
- [ ] ブランドカラー
- [ ] favicon
- [ ] OGP画像
- [ ] LP画像
- [ ] パンフレット
- [ ] 製品カタログ
- [ ] 営業デモ資料
- [ ] スクリーンショットに実顧客情報が含まれていない
- [ ] 使用素材の権利確認が完了している

## 9. 公開判定

| 判定 | 条件 |
| --- | --- |
| 公開可 | Critical / Highが0件、主要動線がすべて成功 |
| 条件付き公開 | Medium以下の既知課題のみで、回避策が明確 |
| 公開延期 | CriticalまたはHighが1件以上 |

最終判定: 要入力
判断理由: 要入力
次回確認日: 要入力
