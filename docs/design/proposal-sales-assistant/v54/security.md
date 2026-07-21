# Security

## 守ること

- APIキー、Authorization、token、passwordを画面・ログ・レスポンスに出さない。
- 内部ファイルパスを返さない。
- admin以外のExportを拒否する。
- Feature Flag OFF時はExportを拒否する。
- Human Review未承認時はExportを拒否する。
- 生成失敗時も安全なエラーメッセージのみ返す。
- PPTXファイル名はpath traversalできない形に安全化する。

## UI

- 失敗時もProposal PreviewとSales Assistant結果は保持する。
- RetryはExportだけを再実行する。
- JSON表示は初期状態では閉じる。
- Beautiful.ai URLは成功時のみ表示する。

## 監査ポイント

- secret候補の混入
- `Content-Disposition`の安全性
- 0 byteや破損PPTXの返却防止
- 権限不足時の403
- 未認証時の401
