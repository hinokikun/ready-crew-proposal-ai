# Version 25.0 Japanese Text Audit

## 目的

正式版公開前に、利用者へ表示される日本語、管理者向け表示、運用ドキュメントに文字化けが残っていないか確認します。

## 確認対象

- Frontend の利用者向け UI 文言
- Backend の API エラー文、履歴名、Analytics 表示名
- README と docs 配下の運用文書
- UAT、Release、Incident、Security 関連ドキュメント

## 検出方針

以下のような mojibake 由来の文字列を検索します。

- `繝`
- `縺`
- `譛`
- `謠`
- `逕`
- `蜊`
- `隕`
- `鬆`
- `邂`

PowerShell で表示だけが文字化けする場合があるため、最終確認は UTF-8 として Python から読み取ります。

## 修正済み項目

- Analytics の「未登録ユーザー」
- Analytics の「提案書作成」
- Analytics の「要約PPT」
- Analytics の「詳細PPT」
- Analytics の「見積PDF」
- Analytics の「フィードバック送信」
- CRM のデフォルト案件名「提案準備案件」
- 監査ログ対象名の「提案書生成」「要約PowerPoint」「見積書PDF」

## 確認コマンド

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q tests\test_security.py
```

全体確認では以下も実行します。

```powershell
git diff --check
```

## 運用ルール

- 新しい UI 文言やドキュメントを追加した後は、UTF-8 で保存されていることを確認します。
- PowerShell の表示文字化けだけで判断せず、ブラウザ表示または Python 読み取りで確認します。
- 文字化けを見つけた場合、意味を推測できない文言は勝手に補完せず、担当者へ確認します。
