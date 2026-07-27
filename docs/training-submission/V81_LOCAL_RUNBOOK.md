# Version81 Local Runbook

Ready Crew Proposal AI / ProposalPilot
Windows Local Runbook

作成日: 2026-07-26

---

## 1. 使用するプロジェクト

必ず次のプロジェクトを使用します。

```powershell
C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai
```

旧プロジェクトをFrontendとBackendの起動に混在させないでください。

---

## 2. 起動前チェック

```powershell
Set-Location -LiteralPath "C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai"
git status --short
git diff --check
```

確認すること:

- `.env` や `.env.local` の中身を画面共有しない。
- APIキー、Password、Token、DATABASE_URLの実値を発表資料へ貼らない。
- 不要なサーバーが3000、3001、8000番で起動していないか確認する。

---

## 3. Backend起動

### 3.1 フォルダ移動

```powershell
Set-Location -LiteralPath "C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai\backend"
```

### 3.2 依存関係確認

初回または環境が変わった場合のみ実行します。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3.3 起動

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

期待状態:

- `http://127.0.0.1:8000/health` が応答する
- DB接続エラーがない
- APIキーやSecretの実値がログに出ない

---

## 4. Frontend起動

### 4.1 フォルダ移動

```powershell
Set-Location -LiteralPath "C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai\frontend"
```

### 4.2 環境変数確認

`frontend/.env.local` は次の形式にします。

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

値にAPIキーやPasswordは入れません。

### 4.3 依存関係確認

初回または環境が変わった場合のみ実行します。

```powershell
npm.cmd install
```

### 4.4 起動

```powershell
npm.cmd run dev
```

期待状態:

- 通常は `http://localhost:3000` で開く
- 3000番が使用中の場合は、Next.jsの案内に従って3001番などを使う
- Backend API Base URLが `http://localhost:8000` を向いている

---

## 5. ログイン後の確認

1. ブラウザでFrontendを開く。
2. ログインする。
3. Proposal Studioを開く。
4. `V81_DEMO_DATA.md` のコピー用案件入力文を貼り付ける。
5. Sales Strategy確認を実行する。
6. Proposal Strategy Workspaceを確認する。
7. Story候補、Presentation Tone、Strategy Scoreを確認する。
8. Presentation Designer AIを確認する。
9. Presentation Quality Engineを確認する。
10. 必要に応じてPPTX生成を確認する。

---

## 6. よくある起動トラブル

### Backendに接続できない

確認:

- Backendが8000番で起動しているか
- `frontend/.env.local` が `http://localhost:8000` を向いているか
- Firewallや別プロセスが妨げていないか

対応:

- Backendターミナルのエラーを確認する
- 別プロセスを止める場合は、Ready Crewプロジェクト由来であることを確認してから止める

### ログインできない

確認:

- Backend DBにユーザーが存在するか
- `APP_AUTH_SECRET` が設定されているか
- 初期管理者を使う場合は `INITIAL_ADMIN_EMAIL` と `INITIAL_ADMIN_PASSWORD` が設定されているか

注意:

- Passwordの実値を発表資料やチャットに貼らない

### Proposal Studioが開かない

確認:

- Frontend buildエラーが出ていないか
- Browser Consoleに認証エラーが出ていないか
- Backend APIが401 / 403 / 500を返していないか

### PPTX生成が失敗する

確認:

- BackendログにPPTX生成エラーがないか
- `python-pptx` 関連依存が入っているか
- 入力データが空でないか

代替:

- デモではPresentation Quality EngineとDesigner AIまで説明し、生成済みサンプルを見せる

---

## 7. 終了方法

BackendとFrontendそれぞれのターミナルで `Ctrl+C` を押して終了します。

終了後に必要なら確認します。

```powershell
git status --short
```

---

## 8. 発表当日の最小コマンド

Backend:

```powershell
Set-Location -LiteralPath "C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai\backend"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```powershell
Set-Location -LiteralPath "C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai\frontend"
npm.cmd run dev
```

ブラウザ:

```text
http://localhost:3000
```
