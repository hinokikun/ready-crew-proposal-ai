# Observability Design

## Events

ログイン成功/失敗、Proposal作成、Autosave失敗、AI生成開始/成功/失敗、処理時間、Token使用量、外部API費用、PPTX生成、PDF生成、Beautiful.ai生成、品質エラー、権限エラー、Workspace境界違反、Job停滞、出力失敗、ユーザー操作、管理者操作。

## Metrics

- proposal_generation_count
- proposal_generation_duration_ms
- pptx_generation_duration_ms
- beautiful_ai_success_rate
- quality_score_average
- red_flag_rate
- autosave_failure_rate
- auth_failure_rate
- workspace_violation_count

## Safe Logging

request_id、user_id、role、organization_id、workspace_id、operation、status、duration_ms、error_typeを記録する。パスワード、APIキー、Token、秘密情報、顧客本文全文、個人情報は記録しない。

## Future Monitoring

Job queue dashboard、外部API費用、LLM token usage、Error budget、Feature Flag利用率を追加する。

