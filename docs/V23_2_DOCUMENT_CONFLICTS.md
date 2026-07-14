# Version 23.2 Document Conflicts

目的: 既存マニュアル・手順書との矛盾候補を、既存ファイルを修正せずに記録します。

## 確認対象

- `docs/V23_1_GITHUB_PUSH_GUIDE.md`
- `docs/V23_1_GITHUB_ACTIONS_GUIDE.md`
- `docs/V23_1_VERCEL_GUIDE.md`
- `docs/V23_1_RENDER_GUIDE.md`
- `docs/V23_1_BROWSER_VERIFICATION.md`
- `docs/V23_1_SIMPLE_UAT.md`
- `docs/USER_MANUAL_TEXT.md`
- `docs/ADMIN_MANUAL_TEXT.md`

## 矛盾候補 1: commit方針

V23.1:

- Version 23.0中心の単一commit例を提示しています。

V23.2:

- 変更がVersion 17〜23.1まで混在しているため、複数commitへ分ける案を提示しています。

提案:

- 実際のpush前は V23.2 の `SAFE_COMMIT_PLAN` を優先してください。
- V23.1 guideは「単純にVersion 23.0だけをcommitする場合」の補助資料として扱ってください。

## 矛盾候補 2: 変更件数

V23.1:

- 作成時点の未コミット数を記録しています。

V23.2:

- V23.2 docs追加前の棚卸しで162件を記録しています。
- V23.2 docs追加後はさらに未追跡docsが増えます。

提案:

- 件数は必ず最新の `git status --short` で確認してください。

## 矛盾候補 3: 本番確認の対象

V23.1:

- Version 23.0ブラウザ確認を中心にしています。

V23.2:

- Version 17〜23.1の混在変更をcommit分割し、Cloud反映順まで扱います。

提案:

- 本番反映前のcommit整理はV23.2を優先。
- ブラウザ操作確認はV23.1を優先。

## 矛盾候補 4: Beautiful.ai status direct access

V23.1:

- Beautiful.ai statusはログイン必須APIのため、直アクセスでログイン要求が出てもroute存在確認になる場合があると説明しています。

V23.2:

- 同じ方針を維持します。

提案:

- 404とログイン要求を混同しないでください。

## 矛盾候補 5: マニュアル原稿と実画面

`USER_MANUAL_TEXT.md` と `ADMIN_MANUAL_TEXT.md` はUAT前の原稿です。

提案:

- UAT後、実画面のスクリーンショットと文言に合わせて修正してください。
- 現時点ではWord化しない方針を維持してください。
