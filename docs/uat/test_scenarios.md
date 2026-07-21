# UAT Test Scenarios

UATでは以下の架空案件を使用する。実在企業名、個人名、実メール、電話番号、APIキー、Password、Tokenは使用しない。

## 1. 制作会社

- 案件名: ブランドサイト刷新と問い合わせ導線改善
- 顧客: 株式会社サンプルクリエイティブ
- 案件概要: 既存ブランドサイトの情報が古く、事例掲載と問い合わせ導線が弱い。サービス一覧、導入事例、問い合わせフォームを整理し、営業資料と連動するWebサイトへ刷新したい。
- 期待されるStrategy: Customer Experience / Digital Experience
- 期待されるReview状態: reviewedまたはapproved。予算や公開時期が曖昧な場合はHuman Review required。

## 2. SaaS

- 案件名: カスタマーサクセス業務の解約予兆分析
- 顧客: 株式会社サンプルSaaS
- 案件概要: 利用ログと問い合わせ履歴から解約予兆を検知し、CS担当者が優先対応できる仕組みを検討している。初期はPoCでスコアリング精度と運用負荷を評価したい。
- 期待されるStrategy: ROI / Risk Reduction
- 期待されるReview状態: Human Review required。利用ログの範囲、個人情報、評価指標の確認が必要。

## 3. 製造業

- 案件名: 外観検査AIによる不良品検知支援
- 顧客: 株式会社サンプル製作所
- 案件概要: 製造ラインで人手による外観検査を行っており、繁忙時に検査ばらつきが発生する。画像認識AIで候補を提示し、検査員が最終判断するPoCを実施したい。
- 期待されるStrategy: Quality Improvement / Automation
- 期待されるReview状態: Human Review required。精度目標、誤検知時の運用、安全基準の確認が必要。

## 4. 小売

- 案件名: 店舗別需要予測と発注支援
- 顧客: 株式会社サンプルリテール
- 案件概要: 店舗ごとの販売実績、天候、イベント情報をもとに発注量の目安を提示したい。欠品と廃棄の削減を目的に、まず3店舗で検証する。
- 期待されるStrategy: Cost Reduction / Operations Improvement
- 期待されるReview状態: reviewed。データ粒度と対象店舗が不足する場合はHuman Review required。

## 5. 医療

- 案件名: 院内問い合わせ対応チャットボット
- 顧客: サンプル医療法人
- 案件概要: 職員から情報システム部門への問い合わせが多く、対応履歴が属人化している。院内規程とFAQをもとに回答候補を出すチャットボットを検討する。
- 期待されるStrategy: Knowledge AI / Risk Reduction
- 期待されるReview状態: Human Review required。医療情報、個人情報、回答責任範囲の確認が必要。

## 6. 教育

- 案件名: 学内ナレッジ検索と教職員向けFAQ
- 顧客: サンプル学園
- 案件概要: 学内規程、申請手順、過去問い合わせを横断検索できず、教職員の確認負荷が高い。生成AIを使った検索補助を検討する。
- 期待されるStrategy: Knowledge AI / Productivity
- 期待されるReview状態: Human Review required。参照範囲、誤回答時の注意、権限分離の確認が必要。

## 7. 人材

- 案件名: 求人票作成と候補者推薦文の標準化
- 顧客: 株式会社サンプルHR
- 案件概要: 営業担当ごとに求人票や推薦文の品質がばらついている。過去案件とヒアリング内容から、求人票の初稿と推薦文テンプレートを作成したい。
- 期待されるStrategy: Quality Standardization / Sales Enablement
- 期待されるReview状態: Human Review required。個人情報や候補者情報の扱いを確認する。

## 8. 建設

- 案件名: 現場報告書のAI-OCR入力支援
- 顧客: 株式会社サンプル建設
- 案件概要: 紙の現場報告書を手入力しており、入力遅延と転記ミスが発生している。AI-OCRで読み取り候補を提示し、担当者が確認後に既存システムへCSV連携したい。
- 期待されるStrategy: Automation / Quality Improvement
- 期待されるReview状態: Human Review required。帳票種類、読み取り精度、CSV項目、確認フローの確認が必要。

## 9. 不動産

- 案件名: 物件問い合わせ対応と営業履歴整理
- 顧客: 株式会社サンプル不動産
- 案件概要: Web問い合わせ後の営業対応履歴が担当者ごとに分散している。問い合わせ内容、希望条件、対応履歴を整理し、次アクションを提案する営業支援を検討する。
- 期待されるStrategy: Sales Productivity / Customer Experience
- 期待されるReview状態: reviewedまたはHuman Review required。個人情報とCRM連携範囲を確認する。

## 10. IT

- 案件名: 社内システム問い合わせのRPA連携
- 顧客: 株式会社サンプルITサービス
- 案件概要: 社内システムの定型申請が多く、問い合わせ対応後に複数システムへ手作業登録している。チャット受付、申請内容確認、RPA連携で処理時間を削減したい。
- 期待されるStrategy: Automation / DX
- 期待されるReview状態: Human Review required。対象システム、権限、例外処理、監査ログの確認が必要。

## 実施方法

各案件について以下を確認する。

1. Sales Assistant Brief
2. Strategy Brief summary
3. Human Review理由
4. Proposal Preview
5. Export可能条件
6. PPTXダウンロード
7. Beautiful.ai有効時のURL表示
