# Version81 Submission Package

Ready Crew Proposal AI / ProposalPilot

作成日: 2026-07-26

---

## 1. パッケージの目的

このSubmission Packageは、Version81で実装した内容を研修提出・発表で第三者が確認できるように整理した提出用一式です。

Version81はFeature Freeze済みです。新機能追加、リファクタリング、大規模修正は行わず、提出に必要な説明資料だけを対象とします。

---

## 2. 提出対象

| 区分 | ファイル | 役割 |
|---|---|---|
| 入口 | `docs/training-submission/SUBMISSION_PACKAGE.md` | 提出物全体の目次 |
| 1ページ要約 | `docs/training-submission/SUMMARY.md` | 目的、成果、技術、今後の課題を1ページで説明 |
| 完了報告 | `docs/training-submission/V81_COMPLETION_REPORT.md` | Version81全体の実装説明 |
| 提出チェック | `docs/training-submission/V81_SUBMISSION_CHECKLIST.md` | 提出前確認、対象外ファイル、セキュリティ確認 |
| デモ台本 | `docs/training-submission/V81_DEMO_SCRIPT.md` | 発表時の操作順と説明台本 |
| デモデータ | `docs/training-submission/V81_DEMO_DATA.md` | 入力用の架空案件 |
| ローカル起動 | `docs/training-submission/V81_LOCAL_RUNBOOK.md` | Windowsでの起動手順 |
| 構造説明 | `docs/training-submission/PROJECT_STRUCTURE.md` | 主要ディレクトリ、主要ファイル、AI Engine、画面 |
| デモ成果物 | `docs/training-submission/DEMO_OUTPUTS.md` | 一時生成したPPTX / JSON / Quality Reportの一覧 |
| PPTX品質レビュー | `docs/training-submission/V81_PPTX_QUALITY_REVIEW.md` | 生成済みPPTXのHuman Quality Reviewと提出判定 |

---

## 3. 任意提出対象

次のデモ成果物は、発表補助として任意で添付します。

| 成果物 | 用途 |
|---|---|
| `V81_demo_detailed.pptx` | 詳細PPTXのサンプル |
| `V81_demo_summary.pptx` | 要約PPTXのサンプル |
| `V81_quality_report.json` | Presentation Quality Engineの結果確認 |
| `V81_sales_strategy_brief.json` | Sales Strategy AIの出力確認 |
| `V81_strategy_workspace_sample.json` | Strategy Workspaceの承認済みサンプル |
| `V81_demo_detailed_polished.pptx` | 文字化け修正後の詳細PPTX |
| `V81_demo_summary_polished.pptx` | 文字化け修正後の要約PPTX |
| `V81_quality_report_polished.json` | polished版Quality Report |

保存場所:

```text
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts
```

---

## 4. 提出対象外

| 除外対象 | 理由 |
|---|---|
| `.env` / `.env.local` | APIキー、Secret、接続先を含む可能性がある |
| `backend/app.db` / `*.sqlite` / `*.db` | ユーザー情報、履歴、ローカルデータを含む可能性がある |
| `node_modules/` | 依存パッケージ本体で提出不要 |
| `.next/` | Frontend build生成物 |
| `.pytest_cache/` / `__pycache__/` | テスト・Python実行キャッシュ |
| `test-results/` / `playwright-report/` | ローカルE2E結果の一時生成物 |
| APIキー、Password、Token、DATABASE_URLの実値 | 秘密情報のため提出禁止 |
| 実顧客名、実メールアドレス、実電話番号 | 研修提出では架空データのみ使用 |

---

## 5. 最終判定

Version81 Submission Packageは提出可能です。

判定:

```text
READY FOR SUBMISSION
```

理由:

- Completion Report、Demo Script、Demo Data、Runbookが揃っている。
- Version81の実装範囲、未実装範囲、Version82候補が明確である。
- デモ用PPTXとJSONサンプルを外部APIなしで一時生成済み。
- PPTX Human Quality Reviewを実施し、提出推奨ファイルを明確化済み。
- 提出対象外の秘密情報、DB、キャッシュ類を明確に除外している。
- Git commit / push / deployは実行していない。
