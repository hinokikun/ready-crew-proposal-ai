# PPTX Visual Regression

Version 22.2では、PPTX生成の分割に合わせて構造回帰テストを追加した。

## 目的

- 詳細PPTXと要約PPTXのスライド数、順序、タイトル、主要図形数を固定する。
- PowerPointとして開けない破損ファイルを検知する。
- 空白スライド、壊れたrelationship、表や図形の大きな欠落を検知する。
- バイナリ完全一致は求めない。生成時刻などで差分が出るため。

## Snapshot

| Snapshot | 対象 |
| --- | --- |
| `backend/tests/snapshots/detailed_pptx_structure.json` | 通常版PPTX |
| `backend/tests/snapshots/summary_pptx_structure.json` | 要約版PPTX |

## Test

`backend/tests/test_pptx_structure_regression.py`

確認項目:

- MIME type
- ZIP/PPTX header
- file size nonzero
- slide count
- slide width / height
- slide title order
- shape count
- text shape count
- table count
- chart count
- picture count
- font names
- broken relationship count
- blank slideなし

## Optional Preview

補助スクリプト:

- `scripts/render_pptx_preview.py`
- `scripts/compare_pptx_previews.py`

LibreOffice / soffice がある環境ではPPTXをPDFへ変換し、プレビューの差分確認に使える。
変換ツールがない環境では、スクリプトは成功扱いにせず終了コード `2` を返す。

## 運用ルール

- PPTXのデザイン、スライド順、タイトル、構成を変える場合はsnapshotを意図的に更新する。
- UI分割や内部リファクタリングではsnapshot差分が出ないことを確認する。
- クラウド環境でPowerPoint/LibreOfficeプレビューを確認した場合のみ、視覚比較成功として扱う。
