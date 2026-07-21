# Logging Review

## 方針

ログは原因調査に必要な最小情報に限定する。APIキー、Password、Token、Authorization、顧客本文全文、内部ファイルパスは出力しない。

## Level

| Level | 用途 |
| --- | --- |
| DEBUG | ローカル開発時の詳細確認。顧客本文や秘密情報は禁止 |
| INFO | 起動、Feature Flag状態、処理成功の概要 |
| WARNING | Feature Flag不整合、外部サービス一時失敗、入力上限超過 |
| ERROR | 生成失敗、外部API失敗、DB接続失敗。秘密情報とstack全文の露出は禁止 |

## Sales Assistant / Export

- request payload全文をログに出さない。
- Export metadataはslide数、engine mode、statusなどに限定する。
- PPTX downloadでは内部pathを返さない。
- Beautiful.aiではAuthorization、API key、prompt全文をログに出さない。

## Frontend

- E2Eの`console.log`はテスト用のエラー可視化として残している。
- 本番UIではrequest_idなど必要情報だけを利用者へ提示する。

## 追加課題

- Backendの統一logger policyを`docs/SECURITY.md`へ将来統合する。
- request_id連携の網羅性をVersion56以降で監査する。
