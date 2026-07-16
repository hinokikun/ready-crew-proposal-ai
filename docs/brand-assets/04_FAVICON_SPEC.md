# ProposalPilot Favicon仕様

対象: ProposalPilot / AI営業秘書
ステータス: 候補ロゴ選定前の仮仕様

## 1. 方針

Faviconは、正式ロゴ選定後に確定します。現時点ではCandidate A: Pilot Foldのシンボルを仮案として使用します。

優先事項:

- 16x16でも潰れない
- 背景が白でも濃色でも識別できる
- Pの印象が残る
- 細い線や複雑な装飾を使わない
- 外部参照を含めない

## 2. 必要サイズ

| 用途 | サイズ | 形式 |
| --- | --- | --- |
| Browser favicon | 16x16 | PNG / ICO |
| Browser favicon | 32x32 | PNG / ICO |
| Browser favicon | 48x48 | PNG / ICO |
| favicon.ico | 16 / 32 / 48 | ICO |
| Apple Touch Icon | 180x180 | PNG |
| Web App Icon | 192x192 | PNG |
| Web App Icon | 512x512 | PNG |
| Maskable Icon | 512x512 | PNG |
| Windows tile | 150x150 | PNG |
| Windows wide tile | 310x310 | PNG |

## 3. デザイン仕様

推奨:

- 背景: Proposal Blue `#155EEF`
- シンボル: White `#FFFFFF`
- 角丸: 20%程度
- セーフエリア: 外周12%以上
- 最小線幅: 16x16換算で2px以上

避けること:

- Taglineを入れる
- `AI営業秘書` を入れる
- 細いアウトラインだけで構成する
- 複雑なグラデーションを使う
- 影や縁取りに依存する

## 4. Maskable Icon

Maskable 512x512では、中心のシンボルを安全領域内に収めます。

推奨:

- Safe zone: 中央80%
- 背景: Proposal Blue
- シンボル: White
- 外周まで重要情報を置かない

## 5. 確認項目

- [ ] 16x16でPの印象が残る
- [ ] 32x32で識別できる
- [ ] 白背景で見える
- [ ] Dark modeのタブでも見える
- [ ] ブラウザタブで潰れない
- [ ] iOSホーム画面で見える
- [ ] Androidホーム画面で見える
- [ ] Windows tileで見える
- [ ] 外部参照なし
- [ ] 秘密情報なし

## 6. 更新元

- SVG候補: `docs/design/brand-assets/svg/`
- マスターPPTX: `docs/design/brand-assets/ProposalPilot_Brand_Assets_v1.pptx`

正式書き出しは、人がロゴ候補を承認した後に行います。
