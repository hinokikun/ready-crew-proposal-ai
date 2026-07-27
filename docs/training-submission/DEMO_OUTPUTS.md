# Version81 Demo Outputs

Ready Crew Proposal AI / ProposalPilot

作成日: 2026-07-26

---

## 1. 保存場所

デモ成果物はGit管理対象外の一時フォルダへ生成しました。

```text
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts
```

外部APIは呼び出していません。ローカルの既存Backendロジックとmock-safeな入力で生成しています。

---

## 2. 生成済みPPTX

| ファイル | 種別 | ページ数 | 用途 |
|---|---|---:|---|
| `V81_demo_detailed.pptx` | 詳細版PPTX | 12 | 初回生成物。文字化け確認用として保持 |
| `V81_demo_summary.pptx` | 要約版PPTX | 11 | 初回生成物。文字化け確認用として保持 |
| `V81_demo_detailed_before.pptx` | 詳細版PPTX | 12 | 修正前比較用 |
| `V81_demo_summary_before.pptx` | 要約版PPTX | 11 | 修正前比較用 |
| `V81_demo_detailed_polished.pptx` | 詳細版PPTX | 14 | 提出推奨。文字化けと枠外要素を解消 |
| `V81_demo_summary_polished.pptx` | 要約版PPTX | 11 | 提出推奨。文字化けと枠外要素を解消 |

---

## 3. JSON成果物

| ファイル | 内容 | 用途 |
|---|---|---|
| `V81_quality_report.json` | Presentation Quality EngineのQuality Report | Score、Findings、Layout連携、Human Review項目の確認 |
| `V81_sales_strategy_brief.json` | Sales Strategy AIの出力 | Decision Maker、Winning Strategy、Expected Objections、Toneの確認 |
| `V81_strategy_workspace_sample.json` | Proposal Strategy Workspaceの承認済みサンプル | AI案、営業担当編集、差分、Strategy Scoreの確認 |
| `V81_quality_report_polished.json` | polished版Quality Report | 提出推奨PPTXに対応するQuality Report |
| `V81_sales_strategy_brief_polished.json` | polished版Sales Strategy Brief | UTF-8再生成後のStrategy Brief |
| `V81_strategy_workspace_sample_polished.json` | polished版Workspace sample | UTF-8再生成後のWorkspace sample |
| `README.md` | デモ成果物の簡易説明 | 一時フォルダ内の目次 |

---

## 4. Quality Report概要

| 項目 | 値 |
|---|---|
| 生成方式 | ローカルBackend Service |
| 外部API呼び出し | なし |
| 初回Quality Score | 78 |
| polished版Quality Score | 77 |
| 詳細PPTXサイズ | 52,129 bytes |
| 要約PPTXサイズ | 51,072 bytes |
| polished詳細PPTXサイズ | 57,140 bytes |
| polished要約PPTXサイズ | 51,083 bytes |

---

## 5. 発表での使い方

1. Frontendデモが正常に動く場合は、画面操作を優先する。
2. PPTX生成に時間がかかる場合は、生成済みPPTXを開く。提出・発表では `*_polished.*` を優先する。
3. Strategy Workspaceの説明では `V81_strategy_workspace_sample.json` を補助資料として使う。
4. Quality Engineの説明では `V81_quality_report.json` を補助資料として使う。
5. 外部APIの状態に左右されたくない場合は、Beautiful.aiではなくローカルPPTX成果物で説明する。

---

## 6. 注意事項

- 一時フォルダのため、PC再起動やクリーンアップで削除される可能性があります。
- 提出物へ添付する場合は、秘密情報や実顧客情報が含まれていないことを再確認してください。
- PPTXは発表補助用であり、Gitへ含める必須成果物ではありません。
- `.env`、DB、APIキー、Password、Tokenは添付しないでください。
