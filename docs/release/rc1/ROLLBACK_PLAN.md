# RC1 Rollback Plan

Strategy v1 RC1で問題が発生した場合の安全な戻し方。

## 原則

- DB変更はないためDB rollbackは不要
- Migration追加はないためmigration rollbackは不要
- まずFeature Flagで `legacy` に戻す
- `reset --hard` やforce pushは使用しない

## 1. Feature Flagで戻す

環境変数を以下へ変更する。

```text
PRESENTATION_ENGINE_MODE=legacy
```

Render等の実行環境では、必要に応じて再起動または再デプロイを行う。

## 2. 戻した後の確認

- [ ] `/health` が正常
- [ ] `/health/ready` が正常
- [ ] 既存ログインができる
- [ ] 既存案件入力ができる
- [ ] Legacy PPTX生成ができる
- [ ] Quality Gateが動作する
- [ ] Beautiful.ai既存導線が維持される
- [ ] Errorログにstrategy_v1関連の新規失敗が出ていない

## 3. Git rollbackが必要な場合

Feature Flagで解消できない場合のみ、対象commitをrevertする。

例:

```powershell
git revert <target_commit>
git push origin main
```

force pushは行わない。

## 4. Rollback後の記録

以下を記録する。

- 発生日時
- Engine Mode
- 対象案件
- Review状態
- Quality Score
- Red Flag
- 失敗内容
- 戻した方法
- 復旧確認結果

## 5. 再開条件

- 原因が特定されている
- 修正後のテストが成功している
- Human Review手順が更新されている
- Pilot対象者へ再開連絡済み
