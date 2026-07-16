# ProposalPilot App Icon仕様

対象: ProposalPilot / AI営業秘書
ステータス: 候補ロゴ選定前の仮仕様

## 1. 方針

App Iconは、Candidate A: Pilot Foldのシンボルを仮案として設計します。正式採用は人の承認後に行います。

目的:

- アプリのホーム画面で識別しやすい
- ブラウザタブ、PWA、スマートフォンで統一感がある
- BtoB SaaSとして落ち着いた印象を保つ

## 2. 必要サイズ

| 用途 | サイズ | 形式 |
| --- | --- | --- |
| iOS Apple Touch Icon | 180x180 | PNG |
| Web App Icon | 192x192 | PNG |
| Web App Icon | 512x512 | PNG |
| Maskable Icon | 512x512 | PNG |
| Windows Tile | 150x150 | PNG |
| Windows Wide Tile | 310x310 | PNG |

## 3. 推奨デザイン

- 背景: Proposal Blue
- シンボル: White
- 補助アクセント: Emeraldを必要最小限
- 角丸: OS側のマスクに任せる
- セーフエリア: 中央80%
- 文字は入れない

## 4. 避けること

- ProposalPilot全文を入れる
- AI営業秘書の文字を入れる
- Taglineを入れる
- 細い線だけで構成する
- 写真背景を使う
- 複雑なグラデーションを使う
- 他社サービスのロゴを入れる

## 5. Maskable対応

Maskable Iconでは、外周20%に重要要素を置かないようにします。

確認:

- 円形マスクでも中央シンボルが切れない
- 角丸マスクでも切れない
- スクエア表示でも余白が広すぎない

## 6. 確認項目

- [ ] 180x180で識別可能
- [ ] 192x192で識別可能
- [ ] 512x512で粗くならない
- [ ] 150x150で潰れない
- [ ] 16x16 faviconとの一貫性がある
- [ ] 白黒でも成立
- [ ] 外部素材なし
- [ ] 秘密情報なし

## 7. 更新元

- SVG候補: `docs/design/brand-assets/svg/`
- マスターPPTX: `docs/design/brand-assets/ProposalPilot_Brand_Assets_v1.pptx`

正式なPNG書き出しは、ロゴ候補の承認後に行います。
