# Version 23.2 Cloud Release Sequence

目的: commit・push後に人が確認する順序を整理します。

## 1. GitHub commit確認

確認:

- GitHub上の最新commitがローカルでpushしたcommitと一致
- commit messageが想定どおり
- 意図しないファイルが含まれていない

## 2. GitHub Actions

確認:

- Backend pytest
- Frontend build
- Lint and syntax checks
- Frontend Playwright E2E
- Cloud deployment smoke test

注意:

- 古い失敗履歴と最新runを混同しないでください。
- workflow runのcommit hashが最新commitと一致していることを確認します。

## 3. Vercel build

確認:

- 最新DeploymentがReady
- Productionになっている
- branchがmain
- commitがGitHub最新commitと一致
- Root Directoryが`frontend`
- `NEXT_PUBLIC_API_URL`がRender Backend URL
- Serverless Function上限エラーなし
- Build Logsにエラーなし

## 4. Render deploy

確認:

- 最新DeployがLive
- commitがGitHub最新commitと一致
- Logsに`Application startup complete`

## 5. Render health

確認URL:

```text
https://ready-crew-proposal-ai.onrender.com/health
https://ready-crew-proposal-ai.onrender.com/health/ready
```

確認:

- `db_connected`
- `migration_ready`
- `maintenance_mode`
- `mock_ai`
- Beautiful.ai route登録

## 6. Frontend / Backend commit一致

確認:

- Frontend表示のbuild情報
- Backend `/health` のcommit情報
- GitHub最新commit

不一致の場合:

- VercelまたはRenderが古いdeployを配信している可能性があります。

## 7. 通常モード

確認:

- memberでログイン
- Simple Guided UIが初期表示
- 技術情報が出すぎていない

## 8. 詳細モード

確認:

- adminでログイン
- 詳細モードで診断情報を確認できる
- member/viewerには管理者情報が出ない

## 9. member UAT

確認:

- STEP 1 案件入力
- STEP 2 AI作成
- STEP 3 内容確認
- STEP 4 提出前チェック
- STEP 5 出力
- STEP 6 AIレビューと改善
- STEP 7 完了

## 10. admin UAT

確認:

- 管理者メニュー
- UATモード
- Analytics
- Audit Log
- User Management
- Maintenance

## 11. Beautiful.ai

確認:

- status表示
- enabled/configured/mock/maintenance
- disabled理由
- 作成操作
- revision再生成

## 12. PPTX / PDF

確認:

- 要約PPTX
- 詳細PPTX
- 見積PDF
- 出力前にQuality Gateが反映されること

## 13. Workspace分離

確認:

- Workspace切替
- 切替後に案件が混ざらない
- Organization越境が起きない

## 14. 権限確認

確認:

- admin
- manager
- member
- viewer

viewerが生成・編集・承認できないことを確認します。
