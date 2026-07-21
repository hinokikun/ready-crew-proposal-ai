# Maintainability

## 実施した整理

- Sales Assistant APIテストのFeature Flag環境変数セットアップを共通化した。
- Sales Assistant routerのlist型を`list[str]`へ整理した。
- validatorのfield型を明示した。
- DB保存しないExport Deliveryの意図をコメントで補足した。

## 重複コード

| 箇所 | 状態 | 対応 |
| --- | --- | --- |
| Sales Assistant APIテストfixture | 重複あり | 共通helperへ整理 |
| Frontend download timeout | `fetchJson`系と類似 | filename header取得が必要なため現状維持 |
| Human Review gate | backend/frontend双方に存在 | backendを最終判定として維持 |

## Dead Code

明確に削除できる未使用関数は今回確認できなかった。`check:unused`でTypeScript未使用は検出対象になっている。

## 生成物

`__pycache__`、`.pytest-tmp-*`、`test-results`、`playwright-report`はcommit対象外とする。権限エラーの出る古いpytest tmp directoryは削除せず触らない。

## 型品質

- Backend: request schemaとvalidator型を整理。
- Frontend: Version54時点で`typecheck`と`check:unused`を通過。
- 今後、`SalesAssistantProposalPreviewResponse.proposal_response`の`unknown`を段階的に具体型へ寄せる余地がある。
