# Test Plan

## Frontend

- TypeScript typecheck
- unused check
- production build
- E2E
  - サイドバー表示
  - Prompt Builder入力
  - Story Engine表示
  - 3ペイン編集表示
  - Designerテンプレート選択
  - モバイルドロワー
  - 既存Guided Flow回帰

## Backend

- compileall
- pytest
- PPTX生成APIが`design_template`を受け取れること
- 既存PPTX/PDF/Beautiful.ai回帰

## 共通

- git diff --check
- 秘密情報を出力しないこと

