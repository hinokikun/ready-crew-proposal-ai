# Pilot Launch Plan

AI営業秘書を社内で試験導入するための実施計画です。顧客本文、生成本文、APIキー、パスワード、トークンはPilot集計へ保存しません。

## 目的

- 営業担当が「案件メールを貼るだけ」で提案準備に進めるか確認する
- 要約PPT、詳細PPT、見積PDFの作成導線を確認する
- 品質ゲート、上司レビュー、フィードバックが運用に乗るか確認する
- エラーや使いにくさを正式運用前に洗い出す

## 推奨期間

- 1週間から2週間
- 対象ユーザーは最初は5名まで
- 1人あたり最低1案件、可能なら2案件を試す

## 必要な環境変数

Backend / Render:

```text
PILOT_MODE=true
PILOT_START_DATE=2026-07-11
PILOT_END_DATE=2026-07-25
PILOT_MAX_USERS=5
MAINTENANCE_MODE=false
```

## 成功基準

- 対象ユーザーの80%以上が1回以上利用
- 提案書作成成功率80%以上
- 重大エラー0件
- 平均使いやすさ4.0以上
- 実務利用できそう評価70%以上
- 時間短縮を感じた評価70%以上

## 中止基準

- 顧客情報や機密情報の誤保存が疑われる
- ログインや権限管理に重大な問題がある
- PPT/PDF作成が継続的に失敗する
- BackendやDBが不安定で業務に影響する

## 復旧方針

1. `MAINTENANCE_MODE=true` にして新規作成とPPT/PDF作成を停止する
2. Render Logs、Vercel Build Logs、GitHub Actionsを確認する
3. 問題箇所を修正して再デプロイする
4. `/health`、`/health/live`、`/health/ready` とスモークテストを確認する
5. `MAINTENANCE_MODE=false` に戻す

## Pilot終了時

- 管理者メニューの Pilot Dashboard から終了レポートを作成する
- フィードバックMarkdownをコピーして上司または研修担当者へ共有する
- 顧客本文や生成本文はレポートに含めない
