# Version81 PPTX Human Quality Review

Ready Crew Proposal AI / ProposalPilot

作成日: 2026-07-26

---

## 1. 対象ファイル

確認対象ディレクトリ:

```text
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts
```

| ファイル | 存在 | 用途 |
|---|---:|---|
| `V81_demo_detailed.pptx` | あり | 初回生成された通常版PPTX |
| `V81_demo_summary.pptx` | あり | 初回生成された要約版PPTX |
| `V81_quality_report.json` | あり | 初回生成されたQuality Report |
| `V81_sales_strategy_brief.json` | あり | 初回生成されたSales Strategy Brief |
| `V81_strategy_workspace_sample.json` | あり | 初回生成されたStrategy Workspace sample |

補助確認対象:

```text
C:\Users\h_umitsu\AppData\Local\Temp\proposalpilot-v81-phase4
```

上記にはVersion81 Phase4のPPTXサンプル8件が存在していました。

---

## 2. 確認方法

### 実施できた確認

- PPTXファイルの存在確認
- `python-pptx` によるPPTX内部構造確認
- スライド数確認
- テキスト抽出
- 文字化け確認
- Shape数、Text Shape数、Table数、Picture数の確認
- Shape座標、スライド枠外要素の確認
- Text Shape同士の重なり候補確認
- フォントサイズの直接指定値確認
- Quality ReportのScore、Findings、Warnings確認
- Layout Decision、Fallback、Unsupported Layout確認
- Numeric Integrity確認

### 実施できなかった確認

- PNGまたはPDFへのレンダリングによる目視確認
- Microsoft PowerPoint自動操作による実画面確認
- PowerPoint上での手動編集操作確認

理由:

- ローカルの `render_slides.py` は利用可能でしたが、同梱artifact-tool packageの解決で失敗しました。
- `soffice` / `libreoffice` コマンドは検出されませんでした。
- そのため、今回はPPTX内部構造とQuality Reportを根拠に評価しています。

確認していない内容は、確認済みとは扱いません。

---

## 3. 修正前の総合評価

| 対象 | Human Review Score | 自動Quality Score | 判定 |
|---|---:|---:|---|
| 通常版 `V81_demo_detailed.pptx` | 66 / 100 | 78 / 100 | C |
| 要約版 `V81_demo_summary.pptx` | 70 / 100 | 未個別JSONなし | C |

主な理由:

- 日本語の一部が `????` に文字化けしており、提出時に明確に目立つ。
- 通常版、要約版ともに2件の枠外要素があった。
- 8ptテキストが複数あり、最低基準の本文16pt以上には届かない要素がある。
- 表紙の装飾ラベル同士に重なり候補がある。
- ただし、PPTX自体は破損しておらず、スライド数と構造は取得できた。

---

## 4. 修正後の総合評価

修正はアプリ本体ではなく、Git追跡対象外の一時フォルダ内デモ成果物の再生成のみです。コード、DB、API契約、PPTX生成ロジックは変更していません。

| 対象 | Human Review Score | 自動Quality Score | 判定 |
|---|---:|---:|---|
| 通常版 `V81_demo_detailed_polished.pptx` | 82 / 100 | 77 / 100 | B |
| 要約版 `V81_demo_summary_polished.pptx` | 80 / 100 | 未個別JSONなし | B |

総合判定:

```text
B: 軽微な修正後に提出可能
```

提出推奨:

- `V81_demo_detailed_polished.pptx`
- `V81_demo_summary_polished.pptx`
- `V81_quality_report_polished.json`
- `V81_sales_strategy_brief_polished.json`
- `V81_strategy_workspace_sample_polished.json`

---

## 5. 評価項目

| 評価項目 | 点数 | 良い点 | 問題 | 改善案 | 重大度 |
|---|---:|---|---|---|---|
| 表紙の完成度 | 78 | 大きなタイトルとブランド表記がある | 装飾ラベルの重なり候補が残る | PowerPoint上で装飾ラベルの重なりを目視確認 | P2 |
| スライド間の統一感 | 82 | data_driven系の配色とフッターが統一 | Blank layoutベースのためmaster構造は弱い | 将来はMaster/Layout管理を強化 | P3 |
| 情報の優先順位 | 82 | タイトル、KPI、Next Actionが分かれている | 一部KPIスライドが単調 | KPIカードに評価軸ラベルを追加 | P2 |
| 余白と整列 | 80 | 枠外要素は修正後0件 | 画像化未確認のため細かな余白感は未確認 | PowerPointで代表ページを目視確認 | P2 |
| 文字サイズと可読性 | 76 | タイトルは30pt以上中心 | 8ptの装飾・ページ要素が残る | 本文ではなく装飾扱いかを人間が確認 | P2 |
| 情報量の適切さ | 82 | 1スライドあたり文字量は概ね200字台以下 | SummaryのClosingはText Shape数が多め | 発表ではClosingを手短に説明 | P2 |
| タイトルの分かりやすさ | 88 | 文字化け修正後は日本語タイトルが読める | 一部タイトルは汎用的 | 提出時は口頭説明で補う | P3 |
| 図解の分かりやすさ | 78 | Timeline、KPI、Comparison構造がある | 画像化できず実物の視線誘導は未確認 | PowerPointでTimelineとKPIを目視確認 | P2 |
| KPI・数値の見せ方 | 80 | 主要数値を保持し、Numeric Integrityはtrue | 大数値カードの見た目は画像未確認 | 重要数値のサイズ差をPowerPointで確認 | P2 |
| 比較表の見せ方 | 80 | Comparison Tableが使われている | 12pt表テキストがあり、投影時は小さい可能性 | 発表では拡大表示または口頭補足 | P2 |
| Timeline・Roadmapの見せ方 | 80 | フェーズ順に整理されている | 視線誘導は画像化未確認 | PowerPointで矢印・順序を確認 | P2 |
| 色・コントラスト | 82 | Navy / Blue / Cyan系で統一 | 実レンダリングのコントラスト未確認 | 投影環境で確認 | P2 |
| 経営層向け資料としての品質 | 80 | ROI、PoC、次アクションが説明可能 | 8pt装飾と一部Web寄り表現が残る | 発表では戦略・効果測定を中心に説明 | P2 |
| 制作会社の提案書としての品質 | 84 | Web制作会社向けの課題とフローに合う | Sales Strategy側は「採用」語に反応する可能性あり | デモ時は業務改善案件として説明 | P2 |
| PowerPointとしての編集しやすさ | 86 | ShapeとText中心で編集可能 | Master/Layout階層はBlank中心 | 将来は編集用Masterを整備 | P3 |

---

## 6. スライド別評価: 通常版 polished

| No | タイトル | Layout ID / Slide Type | 良い点 | 問題点 | 文字量 | 視認性 | 適合性 | 優先度 | 推奨修正 |
|---:|---|---|---|---|---:|---|---|---|---|
| 1 | AI営業支援導入の提案サマリー | LAYOUT-005 / Cover | タイトルが強い | 装飾ラベル重なり候補 | 130 | 中 | 良 | P2 | 表紙だけPowerPointで目視確認 |
| 2 | 現状課題: 提案作成が属人化している | LAYOUT-007 / Estimate判定 | 課題を比較的整理 | Slide TypeがEstimate寄り判定 | 209 | 中 | 中 | P2 | 発表時は課題ページとして説明 |
| 3 | 競合比較分析 | LAYOUT-007 / Comparison | 比較構造が明確 | 表テキストは小さい可能性 | 255 | 中 | 良 | P2 | 投影時の表可読性確認 |
| 4 | Before / After | LAYOUT-006 / KPI判定 | Before/Afterの流れがある | KPI Layout判定は意味的にややズレ | 162 | 中 | 中 | P2 | 将来Designer判定を改善 |
| 5 | 提案作成フロー | LAYOUT-007 / KPI判定 | Version81の流れを説明できる | 7工程で情報量が多い | 213 | 中 | 中 | P2 | 必要なら口頭で補足 |
| 6 | PoC評価KPI | LAYOUT-008 / KPI判定 | KPI項目が整理される | Timeline寄りLayoutになっている | 132 | 中 | 中 | P2 | PowerPointで見え方確認 |
| 7 | PoCスケジュール | LAYOUT-006 / Estimate判定 | スケジュールを説明できる | Layout IDはKPI寄り | 124 | 中 | 中 | P2 | 人間確認 |
| 8 | 概算費用と範囲 | LAYOUT-006 / Estimate | 予算と範囲が明確 | 金額の見せ方は画像未確認 | 114 | 中 | 良 | P2 | 投影前確認 |
| 9 | 概算見積 | Renderer inserted / Estimate | 追加見積として説明可能 | 重複感がある | 178 | 中 | 中 | P2 | 発表では必要に応じて省略 |
| 10 | 予算適合判定 | Renderer inserted / KPI | 予算観点を補足 | KPIカード単調 | 164 | 中 | 中 | P2 | 口頭補足 |
| 11 | 必須・推奨・オプション対応 | Renderer inserted / Matrix | 対応範囲を整理 | 表現はやや詳細 | 181 | 中 | 良 | P2 | 重要部分だけ説明 |
| 12 | 次のアクション | Renderer inserted / Next Action | Closingとして使える | CTAの強さは標準的 | 143 | 中 | 良 | P2 | 発表ではここを最後に見せる |
| 13 | 関連実績 | Renderer inserted / Case Study | 実績説明枠がある | デモ案件では架空性の説明が必要 | 118 | 中 | 中 | P3 | 架空データと明言 |
| 14 | 受注確率判定 | Renderer inserted / KPI | 営業判断の補助になる | 研修提出では補助扱い | 212 | 中 | 中 | P3 | 必須説明から外してもよい |

---

## 7. スライド別評価: 要約版 polished

| No | タイトル | Layout ID / Slide Type | 良い点 | 問題点 | 文字量 | 視認性 | 適合性 | 優先度 | 推奨修正 |
|---:|---|---|---|---|---:|---|---|---|---|
| 1 | AI営業支援導入ご提案書 | Cover | 表紙として成立 | 装飾ラベル重なり候補 | 127 | 中 | 良 | P2 | 表紙のみPowerPoint確認 |
| 2 | 提案サマリー | Summary | 要点整理に向く | 画像未確認 | 201 | 中 | 良 | P2 | 投影確認 |
| 3 | 現状理解 | Current State | 背景説明に向く | 文字量はやや多い | 244 | 中 | 中 | P2 | 発表では要約して話す |
| 4 | 主要課題 | Problem | 短く分かりやすい | なし | 94 | 良 | 良 | P3 | なし |
| 5 | 提案コンセプト | Proposal | 提案の軸が説明可能 | 文字量はやや多い | 245 | 中 | 良 | P2 | 主要語を口頭強調 |
| 6 | Web戦略 | Timeline / Strategy | Web制作会社案件に合う | Text Shape数が多い | 230 | 中 | 良 | P2 | 投影時確認 |
| 7 | サイトマップ | Structure | Web制作文脈に合う | Version81の中核説明からは外れる | 100 | 中 | 中 | P3 | 必要に応じて省略 |
| 8 | KPI設計 | KPI | 効果測定を説明できる | KPIカード単調の可能性 | 106 | 中 | 良 | P2 | 数値視認性確認 |
| 9 | スケジュール | Timeline | 順序説明に向く | 画像未確認 | 120 | 中 | 良 | P2 | 順序確認 |
| 10 | 費用概算 | Estimate | 費用説明に使える | 文字量は中程度 | 180 | 中 | 良 | P2 | 投影確認 |
| 11 | 今後の進め方 | Next Action | Closingとして説明可能 | 24 text shapesでやや密 | 230 | 中 | 中 | P2 | 発表では口頭で絞る |

---

## 8. P0〜P3問題

### P0

なし。PPTXファイルは破損しておらず、スライド数と内部構造を取得できました。

### P1

修正前:

- 通常版に26件、要約版に5件の日本語文字化け候補がありました。
- 通常版、要約版ともに2件の枠外要素がありました。

修正後:

- 文字化け候補は0件。
- 枠外要素は0件。

### P2

- 8ptの装飾・フッター系テキストが残っています。
- 表紙の装飾ラベルに重なり候補が2件残っています。
- KPI系Layoutが複数ページで使われ、見た目が単調になる可能性があります。
- 要約版ClosingはText Shape数が多く、投影時に密に見える可能性があります。
- PNG/PDFレンダリング目視ができていないため、実際の見た目はPowerPointで確認が必要です。

### P3

- Master/Layout階層はBlank中心で、将来の編集テンプレートとしては改善余地があります。
- Quality Engineは文字化けを専用ルールとして検出できていません。
- Designer AIのSlide Type判定は一部意味的にズレる場合があります。

---

## 9. 修正内容

修正対象は、Git追跡対象外の一時デモ成果物のみです。

| 対象 | 修正前の問題 | 修正内容 | 修正後の効果 |
|---|---|---|---|
| 通常版PPTX | 日本語文字化け26件 | UTF-8スクリプトで再生成 | 文字化け0件 |
| 要約版PPTX | 日本語文字化け5件 | UTF-8スクリプトで再生成 | 文字化け0件 |
| 通常版PPTX | 枠外要素2件 | 同一データで再生成 | 枠外要素0件 |
| 要約版PPTX | 枠外要素2件 | 同一データで再生成 | 枠外要素0件 |
| Quality Report | 旧成果物に紐づくReport | polished版Reportを再生成 | Numeric Integrity確認可能 |

アプリ本体のコード、DB、API、PPTX生成ロジックは変更していません。

---

## 10. Before / After

| 指標 | Before detailed | After detailed | Before summary | After summary |
|---|---:|---:|---:|---:|
| スライド数 | 12 | 14 | 11 | 11 |
| 文字化け候補 | 26 | 0 | 5 | 0 |
| 枠外要素 | 2 | 0 | 2 | 0 |
| Text overlap候補 | 3 | 2 | 3 | 2 |
| 最小フォント直接指定 | 8pt | 8pt | 8pt | 8pt |
| 自動Quality Score | 78 | 77 | 個別なし | 個別なし |
| Numeric Integrity | preserved | preserved | 未個別 | 未個別 |

Scoreは78から77へ微減しました。理由は、文字化け解消により正しい日本語が解析対象となり、diagram / numeric判定が変動したためです。提出品質としては、文字化けと枠外要素が解消されたpolished版を推奨します。

---

## 11. Quality Reportとの差

### 自動評価で検出できている問題

- 箇条書き数が多いスライド
- 同じLayout IDの連続
- 極端に小さい文字
- 枠外要素
- Numeric Integrity
- Layout Decision接続結果

### 自動評価で検出できていない問題

- 日本語文字化けを専用重大度で扱えていない
- 表紙装飾ラベルの重なりを提出品質問題として分類できていない
- Slide Type判定の意味的なズレ
- Summary版とDetailed版の役割差が十分かどうか

### 過大評価されている項目

- title scoreは100ですが、修正前は文字化けタイトルが含まれていました。
- layout scoreは内部Layout ID基準であり、実際の目視品質とは完全には一致しません。

### 過小評価されている項目

- post_render_validationは35ですが、空テキストや装飾小文字を強く減点している可能性があります。
- polished版は提出上の致命問題である文字化けが消えていますが、自動Scoreには十分反映されていません。

### Score 78との整合

修正前のScore 78は、実物品質よりやや高めです。文字化けがあるため、人間評価では66〜70程度が妥当です。修正後のScore 77は、文字化け解消後の提出品質を低めに見積もっており、人間評価では80〜82程度です。

### 今後Quality Engineへ追加すべきルール

- `????` や置換文字を検出する文字化けルール
- 装飾テキストと本文テキストを分ける評価
- 表紙装飾ラベルの重なり検出
- Slide Typeとタイトル意味の整合性チェック
- Summary版Closingの密度チェック

---

## 12. 既知の制限

- PNG/PDFレンダリングによる目視確認は未実施です。
- PowerPoint上での手動編集性は未確認です。
- 最小フォント8ptは残っています。ただし、主に装飾、英字ラベル、ページ要素と推定されます。
- polished版は文字化けを解消していますが、Scoreは自動評価上1点下がっています。
- 実際の提出前には、PowerPointで表紙、比較表、KPI、Timeline、Closingを開いて確認してください。

---

## 13. 提出時の説明方法

発表では次のように説明するのが安全です。

1. 「PPTXはローカルの既存生成ロジックで作成したデモ成果物です。」
2. 「初回生成物に文字化けがあったため、提出用にはUTF-8で再生成したpolished版を使用します。」
3. 「PPTXの数値は変更しておらず、Numeric Integrityは preserved です。」
4. 「画像レンダリング目視は環境制約で未実施のため、発表前にPowerPointで代表スライドを確認します。」
5. 「今回の目的はPPTX全面再設計ではなく、Version81の営業戦略、Designer、Quality連携の提出品質確認です。」

---

## 14. 回帰確認

| 確認 | 結果 |
|---|---|
| PPTX関連pytest | 22件成功 |
| Presentation Quality関連pytest | 成功 |
| Designer AI関連pytest | 成功 |
| Numeric Integrity関連pytest | 成功 |
| `python -m compileall app tests` | 成功 |
| `python -m pip check` | 成功 |
| `git diff --check` | 成功、改行コード警告のみ |

Frontend、API、DBを変更していないため、Frontend build / E2Eは今回の影響範囲外です。

---

## 15. 最終判定

```text
B: 軽微な修正後に提出可能
```

提出推奨成果物:

```text
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts\V81_demo_detailed_polished.pptx
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts\V81_demo_summary_polished.pptx
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts\V81_quality_report_polished.json
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts\V81_sales_strategy_brief_polished.json
C:\Users\h_umitsu\AppData\Local\Temp\ready-crew-v81-demo-artifacts\V81_strategy_workspace_sample_polished.json
```
