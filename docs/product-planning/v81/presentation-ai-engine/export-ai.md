# Export AI

- 責務: PPTX、PDF、Beautiful.ai出力前の安全確認。
- 入力: RenderableSlidePlan, QualityReport, ExportTarget.
- 出力: Export request payload.
- 決定論: Quality Gate完了、権限、Feature Flag、外部API設定。
- AI: Exportそのものには新規AI呼び出しを追加しない。
- フォールバック: Beautiful.ai失敗時はPPTX/PDFを案内。

