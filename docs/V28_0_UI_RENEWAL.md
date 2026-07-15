# Version 28.0 UI Renewal

## 目的

ProposalPilot / AI営業秘書を、正式運用・販売を見据えたBtoB SaaSの画面品質へ整える。

## 実施内容

- ProposalPilotのデザイントークンを追加
- 既存ボタン、カード、入力欄、空状態、フォーカス表示をブランドトーンへ調整
- 一般利用者向け7ステップフローの主要文言を整理
- 「Quality Gate」を一般画面では「提出前チェック」として表示
- Beautiful.aiの利用条件とdisabled理由を日本語で表示
- 管理者向け機能を「管理コンソール」として整理
- 共通UIプリミティブを追加

## 変更しないもの

- Backend API
- DB Schema / Migration
- 認証方式
- Role / Permission
- Organization / Workspace分離
- OpenAI生成内容
- PPTX / PDF生成内容
- Beautiful.ai payload / API仕様
- Quality Gate判定ロジック
- 作成履歴、監査ログの保存仕様

## 既知の注意

既存画面は非常に大きいため、Version 28.0では主要導線と共通スタイルを優先しました。全コンポーネントの完全置換は段階移行とします。
