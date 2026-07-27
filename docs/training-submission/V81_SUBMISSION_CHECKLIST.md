# Version81 Training Submission Checklist

Ready Crew Proposal AI / ProposalPilot
Version81 Training Submission Final Audit

作成日: 2026-07-26

---

## 1. 提出可否チェック

| 確認項目 | 判定 | 補足 |
|---|---|---|
| Version81 Completion Reportが存在する | OK | `docs/training-submission/V81_COMPLETION_REPORT.md` |
| Version81の6 Phaseが説明されている | OK | Phase1〜Phase6を第三者向けに整理済み |
| デモ手順が文書化されている | OK | `V81_DEMO_SCRIPT.md` |
| デモ入力データが文書化されている | OK | `V81_DEMO_DATA.md` |
| ローカル起動手順が文書化されている | OK | `V81_LOCAL_RUNBOOK.md` |
| 秘密情報の実値を文書へ記載していない | OK | 変数名のみ記載 |
| Git commit / push / deployを実行していない | OK | 提出前の人間確認後に実施 |

---

## 2. 提出対象ファイル

研修提出用として、最低限次のファイルを添付または参照します。

| 種別 | ファイル |
|---|---|
| 提出パッケージ目次 | `docs/training-submission/SUBMISSION_PACKAGE.md` |
| 1ページ要約 | `docs/training-submission/SUMMARY.md` |
| 完了報告 | `docs/training-submission/V81_COMPLETION_REPORT.md` |
| 提出チェックリスト | `docs/training-submission/V81_SUBMISSION_CHECKLIST.md` |
| デモ台本 | `docs/training-submission/V81_DEMO_SCRIPT.md` |
| デモデータ | `docs/training-submission/V81_DEMO_DATA.md` |
| ローカル起動手順 | `docs/training-submission/V81_LOCAL_RUNBOOK.md` |
| 構造説明 | `docs/training-submission/PROJECT_STRUCTURE.md` |
| デモ成果物一覧 | `docs/training-submission/DEMO_OUTPUTS.md` |
| PPTX品質レビュー | `docs/training-submission/V81_PPTX_QUALITY_REVIEW.md` |

任意で添付する成果物:

- デモ用PPTX
- デモ用要約PPTX
- デモ用Quality Report
- デモ用Sales Strategy Brief
- デモ用Strategy Workspace sample
- PPTXは `*_polished.*` を提出推奨

---

## 3. 提出しないもの

次のファイルや情報は提出物へ含めません。

| 除外対象 | 理由 |
|---|---|
| `.env` / `.env.local` | APIキー、DB接続先、Secretを含む可能性がある |
| `backend/app.db` | ユーザー情報や操作履歴を含む可能性がある |
| `node_modules/` | 依存パッケージ本体で提出不要 |
| `.next/` | Frontend build生成物 |
| `test-results/` | ローカルテスト結果の一時出力 |
| `playwright-report/` | ローカルE2E結果の一時出力 |
| `.pytest_cache/` / `__pycache__/` | テスト・Python実行キャッシュ |
| APIキー、Password、Token、DATABASE_URLの実値 | 秘密情報のため禁止 |

---

## 4. 発表前チェック

発表直前に次の順で確認します。

1. `V81_COMPLETION_REPORT.md` を開き、説明範囲がVersion81に限定されていることを確認する。
2. `V81_DEMO_SCRIPT.md` を開き、発表時間に合わせて5分版または10分版を選ぶ。
3. `V81_DEMO_DATA.md` の案件文をコピーできる状態にする。
4. Backendを起動する。
5. Frontendを起動する。
6. ログインできることを確認する。
7. Proposal Studioを開けることを確認する。
8. Sales Strategy Reviewを開けることを確認する。
9. Proposal Strategy Workspaceで編集、差分、Strategy Scoreが表示されることを確認する。
10. Presentation Designer AIでLayout候補とBefore / Afterが表示されることを確認する。
11. Presentation Quality EngineでScore、Findings、Auto Fixが表示されることを確認する。
12. PPTX生成ボタンを押す場合は、発表前に一度だけ正常生成を確認する。

---

## 5. Git確認

提出前に人間が次を確認します。

```powershell
git status --short
git diff --check
```

確認観点:

- 不要な秘密情報ファイルが含まれていないこと。
- 提出資料以外の意図しない変更がないこと。
- APIキー、Password、Token、DATABASE_URLの実値が差分に含まれていないこと。
- commit / pushは発表者の判断で行うこと。

---

## 6. セキュリティ確認

| 確認項目 | 判定 | 補足 |
|---|---|---|
| APIキー実値を文書に記載していない | OK | 環境変数名のみ |
| Password実値を文書に記載していない | OK | ログイン例は記載しない |
| Token / Authorization値を文書に記載していない | OK | 送信方法のみ説明 |
| DATABASE_URL実値を文書に記載していない | OK | 変数名のみ |
| 実顧客名をデモデータに使っていない | OK | 架空のデモ案件 |

---

## 7. 発表で強調するポイント

- Version81は新しいPPTX生成エンジンそのものではなく、提案戦略、資料設計、品質評価をつなぐ改善です。
- AIが自動生成して終わるのではなく、人間が確認、編集、採用するワークスペースを追加しています。
- 提出前に資料品質をスコアと理由で確認できるため、研修課題の「業務で使える改善」として説明しやすくなっています。
- DB永続保存、共同編集、Generation Job、Knowledge AIはVersion82以降の対象です。
