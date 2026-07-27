# Knowledge AI Future Design

## Target Knowledge

過去提案書、受注/失注案件、制作実績、事例、料金表、会社情報、サービス情報、営業FAQ、社内ルール、業界ナレッジ、提案テンプレート。

## Staged Plan

1. Existing DB search: 現在の`proposal_knowledge`とtemplatesを活用。
2. Metadata enrichment: 業種、提案種別、成果、権限を付与。
3. Chunking: 文書を小単位化。
4. Embedding: 外部ベクタDB導入前にSQLite/PostgreSQLで段階検証。
5. RAG: 出典付きでPrompt Builder / Storyへ引用。
6. Governance: Workspace/Organization分離、削除、更新、重複、古い資料警告。

## Security

機密情報、個人情報、顧客名、契約条件を含むため、アップロード時に分類し、引用時には出典と権限を確認する。

