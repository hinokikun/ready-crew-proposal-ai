# RC1 Acceptance Criteria

Strategy v1を正式リリース候補として扱うための条件。

数値はRC1時点の初期基準であり、業務実態に応じて見直し可能とする。

## 必須条件

- [ ] 全Backendテストが成功
- [ ] Frontend typecheck / build / E2Eが成功
- [ ] `legacy` 既定値が維持されている
- [ ] `legacy` 時にStrategy Engineが呼ばれない
- [ ] `strategy_v1` 時にHuman Review未承認の入力がブロックされる
- [ ] `approved` と `approved_with_changes` のみPresentation Context生成可能
- [ ] `reject` と `re_evaluate` はPresentation Context生成不可
- [ ] Critical Red Flagが0件
- [ ] 秘密情報がログ・DB・レポートに保存されない

## 品質基準

| Item | 初期基準 |
|---|---:|
| Quality Score平均 | 80点以上 |
| Grade A/B比率 | 80%以上 |
| Critical Red Flag | 0件 |
| High相当Red Flag | 運用判断で許容 |
| Generic Fallback率 | 20%以下を目標 |
| Human Review通過率 | 80%以上を目標 |
| Strategy v1がLegacy以上のScore | 70%以上を目標 |

## Human Evaluation基準

営業担当がCompare Reportを見て以下を評価する。

| Item | 目標 |
|---|---:|
| 理解しやすさ | 平均4.0以上 |
| 説得力 | 平均4.0以上 |
| 営業で使えるか | 平均4.0以上 |
| 修正量 | 平均3.0以下を目標 |

## リリース不可条件

- Critical Red Flagが1件以上
- Human Reviewを通さずPresentation Contextが生成される
- `legacy` フォールバックが失敗する
- 既存PPT生成が壊れる
- 秘密情報がログまたはレポートに出る
- Organization / Workspace分離に影響がある

## 判定

RC1は以下のいずれかで判定する。

- PASS: 限定運用可能
- CONDITIONAL PASS: 条件付きでパイロット継続
- FAIL: Strategy v1運用停止、legacyへ戻す
