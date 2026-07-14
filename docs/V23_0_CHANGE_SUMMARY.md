# Version 23.0 Change Summary

目的: Simple Guided UI により、一般利用者が「次へ」を押して提案書作成を進められる画面へ整理しました。

## 変更の中心

Version 23.0 では、新しい営業機能、Backend API、DB、Beautiful.ai 仕様、PowerPoint/PDF 仕様は追加せず、既存機能の表示導線を簡単にしました。

主な変更:

- 一般利用者向けに 7 ステップの案内フローを追加
- 通常モードと詳細モードを分離
- Dashboard の初期表示を簡素化
- 提出前チェックを Quality Gate の一般向け名称として表示
- Beautiful.ai が押せない理由を日本語で表示
- Presentation Review と Proposal Optimization を「AIレビューと改善」に統合表示
- 管理者メニューを一般利用者フローから分離
- モバイル表示とアクセシビリティを改善
- E2E テストを追加

## Guided Flow 構成

追加された主な構成:

- `frontend/components/guided-flow/GuidedFlow.tsx`
- `frontend/components/guided-flow/StepNavigation.tsx`
- `frontend/components/guided-flow/StepFooter.tsx`
- `frontend/components/guided-flow/SimpleErrorMessage.tsx`
- `frontend/components/guided-flow/BeautifulAiSimpleCard.tsx`
- `frontend/components/guided-flow/types.ts`
- `frontend/app/styles/guided-flow.css`

## STEP 1 から STEP 7

1. STEP 1: 案件情報を入力
   - 案件メール、議事録、ヒアリングメモを貼り付けます。
   - 主ボタンは「この内容で提案書を作る」です。

2. STEP 2: AIで提案書を作成
   - 案件整理、提案作成、品質確認、スケジュール確認、最終確認を進捗として表示します。
   - 通常モードでは内部AI名を出しすぎず、作業工程中心に表示します。

3. STEP 3: 提案内容を確認
   - 案件概要、課題、提案方針、スケジュール、見積概要、注意事項、AI推測項目を確認します。

4. STEP 4: 品質確認
   - 一般画面では「提出前チェック」と表示します。
   - 完了ボタンは常に見える位置にあります。
   - 未チェック項目がある場合は「あと○項目の確認が必要です」と表示します。

5. STEP 5: 出力方法を選択
   - 要約PowerPoint、詳細PowerPoint、見積PDF、Beautiful.ai を 1 つのカードに整理しています。

6. STEP 6: AIレビューと改善
   - Presentation Review と Proposal Optimization をまとめて表示します。
   - 詳細スコアや内部根拠は折りたたみです。

7. STEP 7: 完了
   - 作成済み提案書、出力、Beautiful.ai リンク、Review 結果、Revision 番号、最終確認状態をまとめます。

## 通常モード

一般利用者向けの初期モードです。

通常モードでは次を見せない方針です。

- Git Commit
- Build Time
- Backend Version
- Migration Version
- request_id
- 内部 Analytics
- Prompt Studio
- Learning Dashboard
- Queue Monitor
- Audit Log
- Integration 内部設定
- 技術的な Feature Flag
- 管理用診断カード

## 詳細モード

admin または必要な確認者が、既存の AI Workspace、ログ、分析、管理機能を確認するための表示です。

一般利用者には詳細モードを強く見せず、管理者の確認用として使います。

## 提出前チェック

Quality Gate を一般利用者向けに「提出前チェック」として表示します。

改善点:

- 完了ボタンを常に表示
- 未チェック数を表示
- 全チェック後にボタンを有効化
- 完了後に「提出前チェックが完了しました」と表示
- Backend の completed / bypassed / download_unlocked と同期する方針

## Beautiful.ai 簡易表示

通常モードでは技術条件を直接表示しません。

表示例:

- 利用可能: `Beautiful.aiでプレゼンを作成できます`
- 利用不可: `Beautiful.aiを利用するには、次の確認が必要です`

無効理由例:

- 提出前チェックが完了していません
- Beautiful.aiの設定が完了していません
- 現在メンテナンス中です
- 他の出力処理を実行中です
- このアカウントには作成権限がありません

## AIレビューと改善

Presentation Review と Proposal Optimization を一般利用者には 1 つのステップとして表示します。

表示順:

1. AIレビューを実行
2. 改善点を確認
3. 採用する改善を選ぶ
4. 改訂版を作成
5. Beautiful.ai で再生成

## 管理者メニュー分離

一般利用者の操作フローに管理者機能を混ぜない方針へ整理しました。

管理者側に寄せるもの:

- User Management
- Organization / Workspace
- Analytics
- Knowledge
- Prompt Studio
- Learning
- Integrations
- Pilot
- Audit Log
- Release
- UAT
- 接続診断

## モバイル対応

確認対象幅:

- 360px
- 390px
- 768px
- 1024px
- 1440px

改善方針:

- スマホは 1 カラム
- ステップ表示は詰まりすぎない表示
- 主ボタンを見つけやすくする
- 表は必要に応じてカード表示へ寄せる
- 管理画面は通常モードでは出しすぎない

## Accessibility

対応方針:

- ボタン名を明確化
- input と label の関連付け
- checkbox label を押しやすくする
- disabled 理由を表示
- aria-live で状態変化を伝える
- details / summary の開閉状態を分かりやすくする
- 色だけに依存しない状態表示
- prefers-reduced-motion を尊重

## E2E 追加内容

追加確認:

- 通常モードが初期表示される
- STEP 1 から STEP 7 のステップナビゲーション
- 提出前チェック完了ボタンが常に見つかる
- 未チェック数が表示される
- 全チェックで完了ボタンが有効になる
- 完了後に Beautiful.ai が有効になる
- Beautiful.ai disabled 理由が表示される
- 一般利用者に技術診断が表示されない
- admin 詳細モードで技術診断が見える
- 管理者メニューが分離される
- Presentation Review と Optimization が統合表示される
- モバイル表示
- キーボード操作
- エラー再試行
- Workspace 切替時のステップリセット
