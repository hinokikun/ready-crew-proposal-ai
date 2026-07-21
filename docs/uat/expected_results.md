# Expected Results and Troubleshooting

## 期待結果

| 項目 | 期待結果 |
| --- | --- |
| Backend起動 | `/health`が成功し、起動ログに致命的エラーがない |
| Frontend起動 | ブラウザでログイン画面が表示される |
| Feature Flag | Sales Assistant / Proposal Preview / Exportが有効時のみ表示・実行可能 |
| Sales Assistant | Strategy BriefとSales Assistant Briefが生成される |
| Proposal Preview | 提案概要、課題、ストーリー、スライド構成、KPI、見積概要が表示される |
| Human Review | 必須案件は承認前Export不可 |
| PowerPoint Export | 成功時にファイル名、サイズ、ダウンロードボタンが表示される |
| PPTX Download | `.pptx`が保存され、PowerPointで開ける |
| Beautiful.ai | 有効時はURL表示、無効時は理由表示 |
| 権限 | member / viewerに管理機能は表示されない |

## 障害切り分け

### Backend起動失敗

- `.venv` が有効か確認する。
- `DATABASE_URL` が設定されているか確認する。
- port 8000が他プロセスで使用されていないか確認する。
- `APP_AUTH_SECRET` が本番で空になっていないか確認する。

### Frontend起動失敗

- `npm install` 済みか確認する。
- `NEXT_PUBLIC_API_URL` がBackend URLを指しているか確認する。
- port 3000が残っていないか確認する。
- `.next` の破損が疑われる場合は、開発サーバーを停止してから再起動する。

### Feature Flag

- Backend: `SALES_ASSISTANT_ENABLED=true`
- Backend: `SALES_ASSISTANT_PROPOSAL_ENABLED=true`
- Backend: `PROPOSAL_EXPORT_ENABLED=true`
- Frontend: `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED=true`
- Frontend: `NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED=true`
- Backendが最終判定。Frontend flagだけではAPIは有効にならない。

### Export失敗

- adminでログインしているか確認する。
- Human Reviewが`Export可能`か確認する。
- Proposal Previewが生成済みか確認する。
- Backendログに`proposal_export_*` error_typeがないか確認する。

### PPTXダウンロード失敗

- Export成功後にダウンロードボタンが表示されているか確認する。
- Networkで`/api/sales-assistant/export/download`のstatusを確認する。
- 401/403の場合は認証・権限を確認する。
- 409の場合はHuman Review状態を確認する。
- 500の場合はBackendログでPPTX整合性エラーを確認する。

### Beautiful.ai失敗

- `BEAUTIFUL_AI_ENABLED`
- `BEAUTIFUL_AI_API_KEY`
- `BEAUTIFUL_AI_API_MODE`
- `BEAUTIFUL_AI_BASE_URL`
- Theme IDやWorkspace IDの必要性
- 管理画面のBeautiful.ai診断

### 権限エラー

- admin以外はSales Assistant管理画面を利用できない。
- member / viewerで管理APIを呼ぶと403になる。
- Token期限切れ時は再ログインする。

## Known Issues

### Critical

現時点でCriticalは確認なし。

### Major

- 本番Render / Vercel上でのVersion54 Export実ファイルUATは人による確認が必要。
- Export履歴はDB保存されず、ブラウザ更新で消える。
- PPTXは永続URLではなく、ダウンロード時に同じ入力で再生成する。

### Minor

- Sales Assistant routerが統合境界として大きい。
- pytest一時ディレクトリに古い権限エラーが残る場合がある。
- READMEとdocs/releaseのFeature Flag説明が一部重複している。

## Pilot Go / No-Go

### Pilot Go

- Backend pytest成功
- Frontend build成功
- compileall成功
- adminログイン成功
- Sales Assistant生成成功
- Proposal Preview生成成功
- Human Review承認後Export可能
- PPTXダウンロード成功
- member / viewerに管理機能が表示されない
- Critical Known Issueなし

### Pilot No-Go

- ログイン不能
- admin権限境界が破れる
- Proposal Preview生成不能
- Human Review未承認でもExportできる
- PPTXが0 byteまたは開けない
- APIキー、Password、Tokenが画面・ログに出る
- Workspace / Organization分離に問題がある
