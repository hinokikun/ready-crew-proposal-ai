# ProposalPilot Version56 UAT Checklist

このチェックリストは、Version41からVersion55までのProposalPilotを社内Pilotで確認するためのUAT手順です。新機能、AIロジック、Proposal品質、Export仕様の変更確認ではなく、既存機能が安全に利用できることを確認します。

## 0. 事前ルール

- 実在顧客名、実メールアドレス、電話番号、APIキー、Password、Token、顧客本文全文は入力しない。
- サンプル案件は `test_scenarios.md` の架空データを使う。
- 失敗時は画面の文言、request_id、ブラウザConsole、Backendログを記録する。
- 本番クラウド確認をしていない項目は「未確認」と書く。

## 1. Windows起動手順

### Backend

```powershell
cd C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai\backend
.\.venv\Scripts\activate
$env:SALES_ASSISTANT_ENABLED="true"
$env:SALES_ASSISTANT_PROPOSAL_ENABLED="true"
$env:PROPOSAL_EXPORT_ENABLED="true"
$env:USE_MOCK_AI="true"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd C:\Users\h_umitsu\Documents\Codex\2026-06-22\web-ai-ready-crew-1-2\ready-crew-proposal-ai\frontend
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
$env:NEXT_PUBLIC_SALES_ASSISTANT_ENABLED="true"
$env:NEXT_PUBLIC_PROPOSAL_EXPORT_ENABLED="true"
npm.cmd run dev
```

### 終了方法

- Frontend terminalで `Ctrl + C`
- Backend terminalで `Ctrl + C`
- 3000番ポートが残った場合は、起動中のNode開発サーバーを確認して終了する。

## 2. Login

| No | 確認項目 | 期待結果 | 結果 |
| --- | --- | --- | --- |
| 1 | adminログイン | 管理者メニューが表示される |  |
| 2 | memberログイン | 管理者メニューが表示されない |  |
| 3 | viewerログイン | 閲覧中心で作成・Export不可 |  |
| 4 | 無効ユーザー | ログイン拒否 |  |

## 3. Sales Assistant

| No | 確認項目 | 期待結果 | 結果 |
| --- | --- | --- | --- |
| 1 | Feature Flag ON | 管理画面にAI営業アシスタントが表示される |  |
| 2 | サンプル案件入力 | Sales Assistant Briefが生成される |  |
| 3 | Human Review理由 | 不足情報やリスクがある場合に表示される |  |
| 4 | JSON表示 | 初期は閉じ、必要時だけ開ける |  |

## 4. Proposal Preview

| No | 確認項目 | 期待結果 | 結果 |
| --- | --- | --- | --- |
| 1 | 提案書を生成 | Proposal Previewが表示される |  |
| 2 | 表示項目 | 提案概要、課題、提案ストーリー、主要スライド構成、KPI、見積概要が表示される |  |
| 3 | Preview失敗 | Sales Assistant結果は保持され、Proposalだけ再生成できる |  |
| 4 | Human Review | Preview上部とExportカードに状態が引き継がれる |  |

## 5. Human Review

| No | 状態 | 期待結果 | 結果 |
| --- | --- | --- | --- |
| 1 | 未レビュー | Review必須案件はExport不可 |  |
| 2 | レビュー済み | Review必須案件はExport不可 |  |
| 3 | 要修正 | Export不可 |  |
| 4 | 再生成推奨 | Export不可 |  |
| 5 | Export可能 | PowerPoint / Beautiful.ai Export可能 |  |

## 6. Export

| No | 確認項目 | 期待結果 | 結果 |
| --- | --- | --- | --- |
| 1 | PowerPoint生成 | 既存PPTX生成を再利用して成功する |  |
| 2 | PPTXダウンロード | `PowerPointをダウンロード`から`.pptx`を保存できる |  |
| 3 | ファイル名 | `ProposalPilot_<案件名>_<YYYYMMDD-HHmm>.pptx`形式 |  |
| 4 | PPTX整合性 | PowerPointで開け、0 byteではない |  |
| 5 | Retry | Export失敗後、Proposal Previewを保持したままExportだけ再試行できる |  |
| 6 | Beautiful.ai | 有効時はURL表示、無効時は理由表示 |  |

## 7. Regression

| No | 確認項目 | 期待結果 | 結果 |
| --- | --- | --- | --- |
| 1 | 通常の7ステップUI | 既存フローが利用できる |  |
| 2 | Quality Gate | 未チェック数と完了状態が正しく表示される |  |
| 3 | 要約PPTX | 既存出力が壊れていない |  |
| 4 | 詳細PPTX | 既存出力が壊れていない |  |
| 5 | 見積PDF | 既存出力が壊れていない |  |
| 6 | Beautiful.ai通常導線 | 既存導線が壊れていない |  |
| 7 | 作成履歴 | 既存履歴表示が壊れていない |  |
| 8 | 監査ログ | 既存ログ表示が壊れていない |  |

## 8. Mobile

| 幅 | 期待結果 | 結果 |
| --- | --- | --- |
| 360px | 横スクロールなし、主ボタンが見える |  |
| 390px | 横スクロールなし、入力欄が操作できる |  |
| 768px | 管理画面が読める |  |
| 1440px | ダッシュボードと管理画面が崩れない |  |
