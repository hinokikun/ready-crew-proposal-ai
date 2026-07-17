# RC1 Pilot Plan

Strategy v1 RC1は、5〜10件程度の実案件または安全なサンプル案件で限定評価する。

## 目的

- Strategy v1が営業担当の判断と合うか確認する
- Human Reviewで修正可能な範囲か確認する
- Quality ScoreとRed Flagが運用判断に使えるか確認する
- Legacyと比較して提案品質が改善するか確認する

## 対象案件

最低5件、可能なら10件を対象とする。

推奨カテゴリ:

- Vision / OCR
- Automation
- CRM
- Knowledge AI
- Conversational AI
- Digital Experience
- Generative AI
- Generic

## 実施手順

1. 対象案件を選定する
2. Strategy Briefを生成する
3. 営業担当がHuman Reviewを行う
4. Quality Evaluatorを実行する
5. Benchmarkに追加してカテゴリ傾向を確認する
6. LegacyとのCompare Reportを作成する
7. 営業担当がHuman Evaluationを記入する
8. PASS / CONDITIONAL PASS / FAILを判定する
9. 改善点を記録する

## 評価方法

| Item | Method |
|---|---|
| Strategy妥当性 | Human Review |
| 提案品質 | Quality Score |
| 重大課題 | Red Flag |
| Legacy比較 | Compare Report |
| 営業利用可否 | Human Evaluation |
| 修正量 | Human Evaluation |

## Review担当

- 営業担当
- 営業マネージャー
- 必要に応じて提案品質レビュー担当

## フィードバック項目

- 案件カテゴリは正しいか
- Personaは正しいか
- Storyは営業現場に合うか
- Main Messageは使えるか
- KPIは具体的か
- Riskは過不足ないか
- Next Actionは商談で使えるか
- Legacyより分かりやすいか
- 修正量は許容範囲か

## 改善サイクル

1. Pilot実施
2. Quality / Compare / Human Evaluationを集計
3. CriticalまたはHigh課題を分類
4. Feature Flagは必要に応じて `legacy` へ戻す
5. 次Versionで改善する対象を決める

## 完了条件

- 5件以上の評価が完了
- Critical Red Flagが0件
- Quality Score平均80点以上
- Human Evaluation平均4.0以上
- Legacy比較でStrategy v1が同等以上の案件が70%以上
- Rollback手順が確認済み
