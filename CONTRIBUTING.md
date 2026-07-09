# Contributing

Ready Crew Proposal AI は社内試験導入を想定したAI業務支援アプリです。変更時は、既存の提案書生成、PPTX、PDF、認証、権限管理を壊さないことを最優先にしてください。

## 開発の流れ

1. Issueで目的と影響範囲を確認します。
2. 小さなブランチで変更します。
3. Frontend build、Backend構文チェック、pytestを実行します。
4. PRテンプレートの確認項目を埋めます。
5. APIキー、パスワード、顧客本文全文を含めていないことを確認します。

## コーディング方針

- Routerには入口処理を置き、ビジネスロジックはservicesへ置きます。
- DBアクセスはrepositoriesへ寄せます。
- Frontendの型はtypesへ寄せます。
- エラー文は利用者が次に何をすればよいか分かる日本語にします。
- 監査ログには本文全文や機密情報を保存しません。

## テスト

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npm run build
```

## セキュリティ

- `.env` / `.env.local` はコミットしません。
- OpenAI APIキーはBackendの環境変数だけに設定します。
- Frontendへ管理者パスワードやAPIキーを渡しません。
- 社外共有前に人が生成物を確認します。
