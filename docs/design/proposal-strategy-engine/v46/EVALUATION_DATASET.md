# Evaluation Dataset

評価データセットは、複数カテゴリの案件を同一形式で登録できるようにする。

## データ構造

| Field | Description |
|---|---|
| `case_id` | 評価ケースID |
| `category` | 評価カテゴリ |
| `fixture_name` | Strategy Engine fixture名 |
| `title` | 評価ケース名 |
| `expected_engine_modes` | 比較対象エンジンモード |

## 最低カテゴリ

| Category Key | Label | 用途 |
|---|---|---|
| `vision_ocr` | Vision / OCR | AI-OCR、画像認識 |
| `automation` | Automation | RPA、業務自動化 |
| `crm_sales_intelligence` | CRM | CRM/SFA、営業管理 |
| `knowledge_ai` | Knowledge AI | 社内検索、ナレッジAI |
| `conversational_ai` | Conversational AI | チャットボット、問い合わせ対応 |
| `digital_experience` | Digital Experience | Web、顧客接点改善 |
| `generative_ai_transformation` | Generative AI | 生成AI導入支援 |
| `generic_consulting` | Generic | 汎用業務改善 |

## 登録方針

- 各カテゴリに複数案件を登録する
- 実顧客名、個人情報、秘密情報は含めない
- 本番DBには保存しない
- 評価fixtureはローカルテスト用の安全なサンプルとして扱う

## Legacy比較

各ケースは原則として `strategy_v1` と `legacy` の2モードで評価できる構造にする。

Version46では比較構造を作ることが目的であり、本番Legacy生成フローには接続しない。
