# Version 23.1 GitHub Push Guide

目的: 人間が PC の前に戻ったあと、Version 23.0 の変更を安全に GitHub へ反映する手順です。

重要:

- このガイドは手順書です。
- 自動 commit / push は行いません。
- 秘密情報が入っていないことを人間が確認してから進めてください。

## 推奨 commit message

```text
Simplify UI with guided proposal workflow
```

## 1. コマンドプロンプトを開く

Windows の検索で `cmd` と入力し、コマンドプロンプトを開きます。

PowerShell を使う場合も手順はほぼ同じです。

## 2. プロジェクトフォルダへ移動

```bat
cd C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai
```

## 3. 現在の状態を確認

```bat
git status
```

確認すること:

- branch が `main` であること
- 変更ファイルが大量にある場合、今回 commit する範囲を絞ること
- `.env` や秘密情報ファイルが含まれていないこと

## 4. 差分を確認

```bat
git diff
```

確認すること:

- APIキー、Password、Token、DATABASE_URL の値が含まれていないこと
- 実顧客情報、個人情報、顧客メール全文が含まれていないこと
- Version 23.0 の Simple Guided UI に関係する変更であること

## 5. Version 23.0 の主要ファイルだけを stage する

大量の未コミット変更があるため、`git add .` は避けてください。

例:

```bat
git add frontend\components\guided-flow
git add frontend\app\styles\guided-flow.css
git add frontend\app\globals.css
git add frontend\components\AppShell.tsx
git add frontend\components\Header.tsx
git add frontend\e2e\app.spec.ts
git add docs\SIMPLE_UI_SPEC.md
git add docs\GUIDED_FLOW.md
git add docs\QUALITY_GATE_UI.md
git add docs\BEAUTIFUL_AI_USER_FLOW.md
git add docs\UAT_CHECKLIST.md
git add docs\ROLE_PERMISSIONS.md
git add docs\ARCHITECTURE.md
git add README.md
```

Version 23.1 の引き継ぎ資料も同じ commit に含める場合:

```bat
git add docs\V23_1_HANDOFF_STATUS.md
git add docs\V23_0_CHANGE_SUMMARY.md
git add docs\V23_1_GITHUB_PUSH_GUIDE.md
git add docs\V23_1_GITHUB_ACTIONS_GUIDE.md
git add docs\V23_1_VERCEL_GUIDE.md
git add docs\V23_1_RENDER_GUIDE.md
git add docs\V23_1_BROWSER_VERIFICATION.md
git add docs\V23_1_UAT_SAMPLE_CASES.md
git add docs\V23_1_SIMPLE_UAT.md
git add docs\V23_1_BUG_REPORT_TEMPLATE.md
git add docs\USER_MANUAL_TEXT.md
git add docs\ADMIN_MANUAL_TEXT.md
git add docs\WORD_MANUAL_PLAN.md
```

## 6. stage された内容を確認

```bat
git status
```

確認すること:

- `Changes to be committed` に意図したファイルだけがあること
- `.env` が含まれていないこと
- 不明なファイルがあれば commit 前に止めること

## 7. stage 済み差分を確認

```bat
git diff --cached
```

確認すること:

- 秘密情報が含まれていないこと
- 実顧客情報が含まれていないこと
- Version 23.0 / 23.1 の目的に合う変更だけであること

## 8. commit する

```bat
git commit -m "Simplify UI with guided proposal workflow"
```

## 9. GitHub へ push する

```bat
git push origin main
```

## 10. GitHub で commit を確認

GitHub のリポジトリを開きます。

確認すること:

- 最新 commit message が `Simplify UI with guided proposal workflow` であること
- commit hash がローカルの最新 commit と一致していること
- 意図しないファイルが含まれていないこと

## 11. GitHub Actions を確認

GitHub の `Actions` タブを開きます。

確認すること:

- 最新 workflow run が今 push した commit に紐づいていること
- Backend pytest が成功していること
- Frontend build が成功していること
- Lint / syntax checks が成功していること
- Playwright E2E が成功していること

## 既存の大量変更がある場合の安全な commit 方法

1. `git status` で変更一覧を確認します。
2. Version 23.0 / 23.1 に関係するファイルだけを `git add ファイル名` で追加します。
3. `git diff --cached` で stage 済みだけを確認します。
4. 不明な変更が混ざっていたら、commit せずに止めます。
5. 必要なら別 commit に分けます。

避ける操作:

- `git add .`
- `git reset --hard`
- `git checkout -- .`
- 秘密情報を確認せずに push
