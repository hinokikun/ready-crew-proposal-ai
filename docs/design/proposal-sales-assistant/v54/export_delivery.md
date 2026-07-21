# Export Delivery

## 方針

Exportは既存生成機能を呼び出す配送層として扱う。PowerPoint生成は既存のPPTX生成サービスを再利用し、Beautiful.ai生成も既存Beautiful.aiサービスを再利用する。

## PowerPoint

1. Exportボタンでメタ情報を取得する。
2. 成功時にファイル名、サイズ、ダウンロードボタンを表示する。
3. ダウンロードボタン押下時に同じExport入力を再検証する。
4. Human Review、Feature Flag、admin権限を再確認する。
5. PPTXを生成し、整合性検査後にStreamingResponseで返す。

DB保存や内部ファイルパスの返却は行わない。

## Beautiful.ai

1. 既存Beautiful.ai生成サービスを呼び出す。
2. 成功時にeditorUrlまたはplayerUrlを表示する。
3. URLコピーと「Beautiful.aiで開く」を提供する。
4. token、Authorization、APIキー、レスポンス全文の不要表示は行わない。

## Export履歴

- 画面内で最新5件のみ表示する。
- ブラウザ更新で消えてよい。
- statusは待機、生成中、成功、失敗、ダウンロード中を区別する。
- 失敗時もProposal Previewは保持し、Exportのみ再試行できる。
