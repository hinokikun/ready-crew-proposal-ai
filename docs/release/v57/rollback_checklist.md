# Rollback Checklist

Pilot中に重大障害が発生した場合の安全な切り戻し確認表です。reset、force push、本番DB直接操作は行わない。

## ロールバック条件

以下のいずれかが発生した場合はRollbackまたはFeature Flag OFFを検討する。

- Critical issueが1件以上
- admin以外が管理機能を利用できる
- Human Review未承認でExportできる
- PPTXが破損または0 byte
- APIキー、Password、Tokenが露出
- Organization / Workspace分離不備
- Export失敗率が高くPilot継続困難

## Feature Flagによる停止

| 操作 | 確認 |
| --- | --- |
| `PROPOSAL_EXPORT_ENABLED=false` | Export停止 |
| `SALES_ASSISTANT_PROPOSAL_ENABLED=false` | Proposal Preview停止 |
| `SALES_ASSISTANT_ENABLED=false` | Sales Assistant停止 |
| `BEAUTIFUL_AI_ENABLED=false` | Beautiful.ai実生成停止 |
| Frontend再デプロイが必要か確認 |  |

## Git Rollback

重大障害でコードを戻す場合は、原則 `git revert` を使う。

```powershell
git status
git log --oneline -5
git revert <target_commit>
git push origin main
```

force pushやresetは使わない。

## Rollback後確認

| 項目 | 結果 |
| --- | --- |
| GitHub Actions |  |
| Render Deploy Live |  |
| Vercel Ready |  |
| `/health` |  |
| `/health/ready` |  |
| adminログイン |  |
| memberログイン |  |
| 既存7ステップUI |  |
| Export停止確認 |  |

## 連絡

- 障害概要:
- 影響範囲:
- 暫定対応:
- 恒久対応:
- 再開条件:
