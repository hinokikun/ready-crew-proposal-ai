# Migration Plan

Version 80ではDB Migrationを追加しません。

## 移行方針

1. 既存Guided Flowをホームに残す
2. 新しいPrompt Builderは既存入力へ反映して提案生成する
3. Presentation Designerは任意の`design_template`を渡す
4. 未指定時は従来の`corporate_clean`相当で生成する

## Rollback

FrontendのサイドバーとStudio差分を戻せば、既存Guided Flow主体の画面に戻せます。DB変更がないためデータRollbackは不要です。

