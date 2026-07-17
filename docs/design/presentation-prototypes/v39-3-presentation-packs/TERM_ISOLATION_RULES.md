# ProposalPilot Term Isolation Rules

Status: design specification only.

## 1. Purpose

Term isolation prevents category leakage. A proposal for AI-OCR should not accidentally mention CMS or site maps. A web renewal proposal should not mention image recognition labels unless the project explicitly includes image AI.

## 2. Rule Types

| Type | Meaning |
|---|---|
| allowed_terms | Terms that are normal for the pack. |
| conditional_terms | Terms allowed only when the project explicitly includes them. |
| prohibited_terms | Terms that should not appear by default in the pack. |

## 3. Pack Rules

| Pack | allowed_terms | conditional_terms | prohibited_terms |
|---|---|---|---|
| Vision / OCR | 画像, 帳票, 読取, 抽出, 項目確認, 精度, 修正率 | API, CSV, RPA, 業務システム | CMS, サイトマップ, UX, CV, 営業パイプライン |
| Automation | 自動化, Bot, 例外処理, キュー, ログ, 監視 | OCR, CRM, API | 認識枠, 等級, CMS, サイトマップ |
| Conversational AI | 質問, 回答, エスカレーション, チャネル, 会話ログ | CRM, ナレッジ検索, FAQ | OCR, 画像分類, CMS |
| Knowledge AI | 文書検索, 根拠, 出典, 検索, RAG, 権限 | 生成AI, チャット, SSO | OCR精度, サイトマップ, 案件更新率 |
| CRM | 顧客, 商談, 活動, 案件, パイプライン, 次アクション | 生成AI, メール, カレンダー | OCR, CMS, サイトマップ, 認識枠 |
| Generative AI | 生成AI, プロンプト, ガイドライン, レビュー, ガバナンス | RAG, ナレッジ, CRM | OCR, CMS, 画像分類 |
| Digital Experience | UX, IA, CMS, コンテンツ, 計測, CV, ページ速度 | AIチャットボット, EC, CRM | OCR, 等級, 認識枠, アノテーション |
| Generic | 課題, 改善, 設計, 実行, 判断, ロードマップ | Any category term if user input includes it | unconditional OCR, RPA, CRM, CMS, chatbot, image recognition terms |

## 4. Leakage Checks

A future test should inspect generated slide text and fail when:

- Vision/OCR-specific words appear in Digital Experience without explicit AI image/OCR input.
- Web-specific words appear in AI-OCR without explicit web input.
- CRM pipeline terms appear in Generic without CRM input.
- Chatbot escalation terms appear in Knowledge AI without chatbot input.
- Generic Pack contains any technical category term as default text.

## 5. Example Failures

- AI-OCR proposal contains CMS, site map, wireframe, or conversion path.
- Web production proposal contains annotation, recognition confidence, or product grade.
- CRM proposal contains OCR read accuracy as a KPI.
- Generic proposal starts with AI recognition visuals without project evidence.

## 6. Required Production Gate

Before Version40 integration, generated decks should run category term isolation checks alongside overflow and broken-relationship checks.
