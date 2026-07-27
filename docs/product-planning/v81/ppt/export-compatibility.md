# Export Compatibility

## PPTX

既存`python-pptx`生成を維持し、Shape中心で編集可能性を保つ。

## PDF

PDFは提出・確認用。PPTXからの変換または既存PDF serviceを利用する。

## Beautiful.ai

Beautiful.aiには公式Prompt APIを利用し、editorUrl / playerUrlを自前生成しない。

## Backward Compatibility

既存`PptxDownloadRequest`は壊さず、`design_template`と`brand_settings`はoptionalのまま扱う。

