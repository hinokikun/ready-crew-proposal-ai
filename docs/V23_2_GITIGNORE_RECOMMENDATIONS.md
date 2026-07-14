# Version 23.2 Gitignore Recommendations

目的: 不要ファイル候補と `.gitignore` の状況を確認し、必要な追加案だけを記録します。

## 現在の `.gitignore` で除外済み

以下は既に除外されています。

- `.env`
- `.env.local`
- `.env.*.local`
- `backend/.env`
- `frontend/.env`
- `frontend/.env.local`
- `.venv/`
- `backend/.venv/`
- `node_modules/`
- `frontend/node_modules/`
- `.next/`
- `frontend/.next/`
- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`
- `dist/`
- `build/`
- `coverage/`
- `*.log`
- `*.db`
- `*.sqlite`
- `*.sqlite3`
- `backend/app.db`
- `playwright-report/`
- `test-results/`
- `frontend/playwright-report/`
- `frontend/test-results/`
- `*.tsbuildinfo`
- `tmp/`
- `outputs/`

## 不要ファイル候補スキャン結果

候補数: 6

候補:

- `docs/SCREENSHOT_LIST.md`
- `docs/USER_MANUAL_TEMPLATE.md`
- `docs/V23_1_BUG_REPORT_TEMPLATE.md`
- `frontend/components/app-shell/logic-parts/outputs.ts`
- `scripts/compare_pptx_previews.py`
- `scripts/render_pptx_preview.py`

判定:

- 上記はファイル名に `screenshot`、`output`、`preview` が含まれるため候補に出ています。
- 実際にはドキュメントまたはテスト支援scriptであり、単純な生成物ではありません。
- commit禁止ではなく、人の確認後commit対象です。

## 追加提案

必要に応じて、将来追加を検討してください。

```text
screenshots/
*.png
*.jpg
*.jpeg
*.webp
*.gif
*.pptx
*.pdf
```

注意:

- 現在は `.gitignore` を変更していません。
- もし公式資料として画像、PPTX、PDFを管理する方針がある場合、上記を追加しないでください。
