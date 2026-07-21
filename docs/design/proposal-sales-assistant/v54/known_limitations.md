# Known Limitations

- Export履歴はDB保存しない。
- ブラウザ更新で履歴は消える。
- PowerPointダウンロードは同じExport入力を再送して生成する。
- 生成済みPPTXの永続URLは提供しない。
- Beautiful.ai URLは既存Beautiful.ai APIレスポンスに依存する。
- member向けExportはVersion54では対象外。
- 本番クラウドの成功確認は人がRender/Vercelで行う。

## Version55候補

- 成果物の永続保存
- Export監査ログ
- member向け承認済みExport
- Export履歴DB化
- ダウンロード期限管理
- Storage連携
