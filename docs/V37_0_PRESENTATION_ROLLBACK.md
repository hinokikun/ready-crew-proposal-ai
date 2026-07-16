# Version 37.0 Presentation Rollback

## 対象

Version 37.0はPPTXデザイン生成層の変更であり、DB、Migration、認証、Organization / Workspace、Beautiful.ai API仕様は変更していない。

## 安全な戻し方

重大なPPTX表示崩れが本番で見つかった場合は、対象commitを `git revert` で戻す。

```
git revert <version-37-commit>
git push origin main
```

`reset --hard` や force push は使用しない。

## 戻した後の確認

1. GitHub Actionsが成功する
2. VercelがReadyになる
3. RenderがLiveになる
4. `/health` と `/health/ready` が正常
5. memberでログインできる
6. AI分析からPPTX生成まで完了する
7. 要約PPTX、詳細PPTX、見積PDF、Beautiful.aiの既存導線が動く

## 影響範囲

戻し対象はPowerPointデザインと関連テスト、ドキュメントのみ。案件データ、ユーザー、監査ログ、作成履歴は削除しない。
