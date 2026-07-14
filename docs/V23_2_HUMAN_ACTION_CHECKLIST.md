# Version 23.2 Human Action Checklist

目的: 人がPCへ戻った後に行うことを最大15項目にまとめます。

## チェックリスト

1. コマンドプロンプトまたはGit Bashを開く。
2. プロジェクトへ移動する。
   ```bat
   cd C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai
   ```
3. 現在のGit状態を確認する。
   ```bat
   git status --short
   ```
4. `docs/V23_2_SECRET_AUDIT.md` を確認し、秘密情報候補を人が確認する。
5. `docs/V23_2_SAFE_COMMIT_PLAN.md` を開き、commit順を確認する。
6. Commit 1 の対象だけを `git add` する。
7. stage済み差分を確認する。
   ```bat
   git diff --cached --stat
   git diff --cached
   ```
8. 問題なければcommitする。
9. commit後に `docs/V23_2_TEST_MATRIX.md` の該当テストを実行する。
10. Commit 2以降も同じ流れで進める。
11. 最終commit後に全テストを実行する。
12. `git log --oneline -8` でcommit列を確認する。
13. `git push origin main` を実行する。
14. `docs/V23_2_CLOUD_RELEASE_SEQUENCE.md` に沿ってGitHub Actions、Vercel、Renderを確認する。
15. `docs/V23_1_BROWSER_VERIFICATION.md` と `docs/V23_1_SIMPLE_UAT.md` で本番ブラウザUATを行い、不具合は `docs/V23_1_BUG_REPORT_TEMPLATE.md` に記録する。

## 最初に見るファイル

最初に見るべきファイル:

```text
docs/V23_2_SECRET_AUDIT.md
```

理由:

- 秘密情報が混ざっている状態でcommitしないためです。

## 最初に実行するコマンド

```bat
git status --short
```
