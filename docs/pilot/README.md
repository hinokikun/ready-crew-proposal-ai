# Pilot Sprint 1 Real Proposal Validation

Pilot Sprint 1では、ProposalPilot Strategy v1を実案件または安全なサンプル案件で評価する。

今回の目的は新機能開発ではなく、営業担当が実際に使える品質かを確認し、改善点を整理することである。

## 対象

- 5〜10件の案件
- Legacy EngineとStrategy v1の比較
- Proposal Quality Report
- Human Review Report
- 営業担当によるHuman Evaluation

## 使うテンプレート

| File | Purpose |
|---|---|
| `PILOT_DATASET_TEMPLATE.md` | 評価対象案件を登録する |
| `HUMAN_EVALUATION_TEMPLATE.md` | 営業担当が案件ごとに評価する |
| `PILOT_SUMMARY_TEMPLATE.md` | 複数案件の結果を集計する |
| `IMPROVEMENT_BACKLOG_TEMPLATE.md` | 改善事項を管理する |

## 運用手順

1. Pilot対象案件を5〜10件選ぶ
2. `PILOT_DATASET_TEMPLATE.md`へ案件を登録する
3. 各案件でLegacyとStrategy v1の評価結果を確認する
4. 営業担当が`HUMAN_EVALUATION_TEMPLATE.md`を記入する
5. 結果を`PILOT_SUMMARY_TEMPLATE.md`へ集計する
6. 改善事項を`IMPROVEMENT_BACKLOG_TEMPLATE.md`へ登録する
7. 優先度を付けて次Sprintで対応する

## 注意事項

- 実顧客名、個人情報、秘密情報は記録しない
- APIキー、Password、Tokenは記録しない
- 顧客本文全文は貼り付けない
- 評価コメントには必要最小限の要約だけを書く
- 本番生成ロジックの変更判断は、Pilot結果を確認してから行う

## 完了条件

- 5件以上の評価が完了している
- 営業担当の評価が記録されている
- LegacyとStrategy v1の比較結果が整理されている
- 改善Backlogに優先度が付いている
- Criticalな問題がある場合は本番利用を止める判断ができる
