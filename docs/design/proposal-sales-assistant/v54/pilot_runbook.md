# Pilot Runbook

## Windowsローカル起動

1. PowerShellまたはコマンドプロンプトを開く。
2. プロジェクトフォルダへ移動する。
3. Backend環境変数を確認する。
4. `SALES_ASSISTANT_ENABLED=true`
5. `SALES_ASSISTANT_PROPOSAL_ENABLED=true`
6. `PROPOSAL_EXPORT_ENABLED=true`
7. 必要に応じて`BEAUTIFUL_AI_ENABLED=true`
8. Backendを起動する。
9. Frontendを起動する。
10. ブラウザでFrontend URLを開く。

## 確認手順

1. adminでログインする。
2. 詳細モードを開く。
3. AI営業アシスタントを開く。
4. サンプル案件を入力する。
5. Sales Assistant Briefを生成する。
6. Proposal Previewを生成する。
7. Human Reviewを`Export可能`へ変更する。
8. PowerPoint生成を押す。
9. 成功後に`PowerPointをダウンロード`を押す。
10. `.pptx`が保存され、0 byteでないことを確認する。
11. PowerPointで開けることを確認する。
12. Beautiful.ai生成を押す場合はURLが表示されることを確認する。

## サンプル案件

実在企業名、実メールアドレス、APIキー、パスワード、顧客本文全文は使用しない。

## ログ確認

- Backend terminal
- Frontend terminal
- ブラウザConsole
- Network tab

クラウド確認はRender/Vercel上で人が実施する。
