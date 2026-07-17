# ProposalPilot Category KPI Packs

Status: design specification only.

## 1. Universal KPI Display Model

Every KPI should be expressed as one of four fields:

| Field | Meaning |
|---|---|
| Baseline | Current value or current state before improvement. |
| Target | Desired value or target condition. |
| Measurement | How the value will be measured. |
| Decision Criterion | What condition supports go/no-go or rollout decision. |

If numbers are unavailable, show status labels instead of inventing values:

- 未測定
- PoCで測定
- PoCで確定
- 合意が必要
- 現状確認中

## 2. Category KPI Packs

| Pack | KPI candidates |
|---|---|
| Vision / OCR | 候補正答率, 読取精度, 人手修正率, 確認時間, 誤登録率 |
| Automation | 自動化対象件数, 成功率, 例外率, 処理時間, 人手作業削減量 |
| Conversational AI | 自己解決率, エスカレーション率, 回答品質, 応答時間, 利用者満足度 |
| Knowledge AI | 検索成功率, 根拠提示率, 回答精度, 探索時間, 利用率 |
| CRM | 入力率, 活動可視化率, 案件更新率, 営業アクション実行率, 商談情報品質 |
| Generative AI | 利用率, 作業時間, 出力採用率, 修正量, リスク検知件数 |
| Digital Experience | コンバージョン関連指標, 離脱, 回遊, ページ速度, 運用更新効率, 問い合わせ |
| Generic | 進捗, 品質, 工数, 利用, 判断基準 |

## 3. Display Rules

- Do not use large fabricated numbers.
- Use dashboard cards only when the meaning is clear.
- Use state chips when values are not available.
- Use measurement method and decision criterion to make the KPI actionable.
- Keep maximum five primary KPIs on one slide.
- Add appendix only if detailed measurement definitions are required.

## 4. Prohibited KPI Behavior

- Do not show win probability unless it is backed by actual CRM data.
- Do not invent percentage improvement.
- Do not reuse Web conversion KPIs in OCR, RPA, CRM, or Generic packs unless the project explicitly includes Web.
- Do not reuse OCR accuracy KPIs outside Vision/OCR unless the project explicitly includes extraction or recognition.
