# Ready Crew Proposal AI Design Concept v1

基準: UI Contract Freeze `72394c2`  
目的: Business Workbenchとしての完成形Visual / UX Directionを定義する  
対象外: 既存TSX/CSS/testsの変更、token実装、Production、Render/Vercel、Feature Flag、OpenAI API、Presentation Master、M30、renderer関連

## 1. PRODUCT DESIGN PRINCIPLE

### 1. 仕事の前進を主語にする

AIの存在ではなく、案件が「次に進める状態」になったかを中心に設計する。各画面には現在地、次の一手、未完了の確認を明確に置く。

### 2. 整理してから生成する

入力、整理、確認、生成、レビュー、Quality Gate、Outputを一続きの業務として見せる。生成結果だけを突然提示しない。

### 3. 人が判断する箇所を尊重する

AIの提案、未確認事項、人が確定した内容を視覚的に分離する。人の承認を装飾ではなく業務上の状態として扱う。

### 4. 忙しい人の認知負荷を減らす

一画面に同じ強さの情報を並べない。Primary Action、Required Attention、Supporting Informationの順に視線を導く。

### 5. 信頼は説明可能な状態表示から作る

「AIが賢そうに見える」より、何を処理中か、何が不足しているか、誰が確認済みか、出力できるかを明確にする。

### 6. 運用画面も業務画面として扱う

管理者画面を技術診断の置き場にせず、頻度、重要度、リスク、状態に基づく運用ワークスペースとして整理する。

### 7. 一貫性は見た目ではなく判断規則で作る

同じ意味の状態、操作、注意、失敗は同じ視覚・文言・優先順位で表現する。ただし利用者と管理者の情報密度は目的に合わせて変える。

## 2. VISUAL PERSONALITY

**calm / precise / operational / trustworthy / focused / human-reviewed / quietly capable**

派手なAIプロダクトではなく、案件を確実に前へ運ぶ、落ち着いた業務ワークベンチとする。

## 3. INFORMATION HIERARCHY

すべての画面で、次の5層を同じ順序で扱う。

| 階層 | 視覚原則 | 代表的な内容 |
|---|---|---|
| Primary Action | 画面内で最も強い操作。原則1つ | 提案書を作る、確認する、完了する、出力する |
| Current State | 現在地と進行状態。常に見える | Step、案件状態、Quality Gate、生成中、確定済み |
| Required Attention | 未入力、警告、承認待ち。強調するが不安を煽らない | 不足情報、Review待ち、接続エラー、出力ロック |
| Supporting Information | 判断を助ける補足 | 案件概要、根拠、メタデータ、履歴、説明 |
| Advanced Information | 必要な人だけ見る詳細 | JSON、診断、ログ、内部指標、拡張設定 |

Primary Actionは色だけでなく、位置、サイズ、周辺余白、文言で優先順位を示す。Advanced Informationは折りたたみ可能にするが、panel id・open条件・E2E契約は維持する。

## 4. CORE USER EXPERIENCE DIRECTION

利用者の基本体験は「入力フォーム」ではなく「案件を提出可能な状態へ整える進行レール」とする。

1. 案件情報を貼り付ける。最初に必要な入力だけを提示する。
2. AI整理結果を、原文と推定・不足情報が混ざらない形で示す。
3. 利用者が内容を確認し、必要な箇所だけ補正する。
4. 生成前に、提案の目的、案件評価、未確認事項を短く確認する。
5. AI生成中は、処理ステージと現在の状態を示し、二重操作を防ぐ。
6. Reviewでは「AI提案」「人の判断」「未確定」を明確に分ける。
7. Quality Gateでは、提出・出力に必要な確認項目を一覧化する。
8. Outputでは、利用可能な形式と、まだロックされている理由を同じ場所で示す。
9. 完了後は、履歴・案件・次アクションへ自然に戻れるようにする。

既存のstep順、CTA名、loading・disabled条件、API発火条件は変更しない。改善対象は、同じ導線をより少ない視線移動と判断負荷で理解できるVisual / UX構造とする。

## 5. ADMIN EXPERIENCE DIRECTION

管理者画面は、機能一覧ではなく「運用上の判断キュー」として構成する。

### 優先順位

| 軸 | 表示方針 |
|---|---|
| 頻度 | 毎日確認する項目を最上段、低頻度設定は後段または折りたたみ |
| 重要度 | 利用継続、品質、権限に関わるものを先に表示 |
| リスク | 削除、bypass、maintenance、retention等は明確なDanger Zoneへ分離 |
| 状態 | 要対応、確認中、正常、情報のみを一目で判別 |

### 管理者の画面構造

- 先頭: システム・ユーザー・品質のReadiness summary
- 次: 要対応の運用キュー
- 次: 頻繁に使うユーザー、利用状況、品質、監査
- 次: 診断・連携・リリース
- 最後: Prompt、Learning、Knowledge等の高度機能
- 危険操作: 通常のPrimary CTAから離し、対象・影響・確認操作を明示

現在の巨大なaccordion構造は、panel id・summary・open状態を保ちながら、視覚的にはカテゴリ、状態、頻度でグルーピングする。すべてのpanelを同じborder・同じ強さで並べない。

## 6. APP SHELL DIRECTION

### Desktop

- Sidebar: 主要業務の現在地と移動先。ブランド装飾ではなくワークスペースの目次。
- Header: product identity、workspace context、global actionsを一列に整理。
- Workspace: 案件の状態、期限、担当、現在のstepを常時理解できる領域。
- Main Content: 一画面一主目的。ページヘッダー、primary action、required attention、supporting informationの順。
- Advanced detail: 主作業を圧迫しない折りたたみ・補助領域。

Sidebarのactive state、role別item、collapse、mobile open、navigation stateはUI Contract Freezeに従い変更しない。

### Mobile

- Sidebarは常設目次ではなく、必要時に開くnavigation drawerとして扱う。
- Headerには現在画面と最重要アクションを優先。
- Current StateとPrimary Actionを最上部に固定的に認識できるようにする。
- Supporting Informationは縦積み、Advanced Informationは後段へ移動。
- 大きなgridを単純縮小せず、1列の判断順に再配置する。
- tableは重要列を優先し、補助列は横スクロールまたは詳細表示へ委譲する。

## 7. VISUAL HIERARCHY

| 要素 | 原則 |
|---|---|
| Page title | 画面の目的を日本語で明示。画面ごとに1つの主見出し |
| Section title | その領域で何を判断・操作するかを表現 |
| Body | 読みやすい行長とline-height。説明は操作の近くに置く |
| Metadata | 主情報より弱く、ただし必要時に探せるコントラスト |
| Status | 色だけに依存せず、ラベル・アイコン・位置で意味を伝える |
| Primary CTA | 現在の主目的に対する操作を1つ。最も強い視覚階層 |
| Secondary CTA | 戻る、補足、再読込、別経路。Primaryと競合させない |
| Danger action | 破壊的・不可逆操作。独立領域、説明、確認を伴う |

見出しを大きくするだけで階層を作らず、余白、配置、情報量、操作の近接性を組み合わせる。

## 8. SURFACE STRATEGY

Surfaceは「背景の上にcardを大量に載せる」構造にしない。

1. App background: 長時間利用で疲れにくい静かなneutral surface。
2. Workspace surface: 現在の案件作業を受け止める主領域。背景と明確に区別する。
3. Section surface: 関連情報をまとめる薄い境界。常に浮かせない。
4. Card surface: 独立した判断単位、KPI、要約、警告に限定。
5. Modal surface: 作業を一時的に遮る確認・入力だけに使用。
6. Drawer surface: mobile navigationや補助操作に限定。

Panelは主作業のまとまり、Cardは独立した判断単位として使い分ける。dashboardはcardの列ではなく、summary → action queue → trend/detailの順で構成する。border、背景、余白、見出しでまとまりを作り、shadowは階層が必要な場合だけ使う。

## 9. COLOR DIRECTION

具体的なHEX値はこの段階では定義しない。色はブランド装飾ではなくsemantic roleとして設計する。

| Role | 用途 |
|---|---|
| Neutral | 背景、surface、本文、境界、補助情報。長時間利用の基盤 |
| Brand | product identity、active navigation、主要な信頼表現 |
| Action | Primary CTA、focus、選択中。操作可能性を示す |
| Success | 完了、確定、利用可能、Quality Gate通過 |
| Warning | 不足、要確認、期限、部分的なリスク |
| Danger | 削除、失敗、停止、不可逆操作 |
| Information | 補足、説明、診断結果、non-blocking notice |
| AI-assisted | AIが整理・提案・処理中であること。BrandやSuccessと混同させない |

AI-assistedは独立した意味を持つが、主役の色にしない。Successは人が確定した状態、AI-assistedはAIが関与した状態として別の意味にする。

## 10. TYPOGRAPHY DIRECTION

- 日本語の長文説明を前提に、文字サイズより行間と行長を優先する。
- Page title、section title、body、label、metadataを明確に分ける。
- 数字はKPI・件数・時間・確率が比較しやすいよう、桁位置と単位を揃える。
- 英数字、API名、version、status codeは本文と混ぜず、metadataまたはtechnical detailとして扱う。
- 管理テーブルは密度を上げても、列名、単位、status、row actionを追跡できるサイズを保つ。
- 長い案件名、企業名、URL、エラーメッセージは折返し・省略・tooltipのルールを持つ。
- 太字を多用せず、weightは情報階層と操作優先順位のために使う。
- すべての情報を大文字・英語eyebrowで始める構成にはしない。日本語業務文脈を主とする。

具体的なfont implementation、font file、font token値はFoundation Designで決定する。

## 11. SPACING / DENSITY DIRECTION

同じDesign Systemのspacing原則を使いながら、密度の目的を変える。

| 画面 | 密度方針 |
|---|---|
| 利用者のホーム | 低〜中密度。次の行動と最近の案件を優先 |
| Proposal flow | 中密度。入力・確認・状態を連続して追える |
| Review / Quality Gate | 中密度。確認項目を比較しやすく、CTAに近づける |
| Output | 低〜中密度。利用可能形式、ロック理由、次アクションを明確に |
| Manager workspace | 中〜高密度。判断材料をまとめるが、Advanced detailは分離 |
| Admin dashboard | 中密度。要対応を優先し、情報のみの指標を弱める |
| Admin table / logs | 高密度。ただし列の意味、行間、status、操作対象を維持 |

余白は装飾ではなく、情報のまとまりと操作の優先順位を示す。同じ意味のsectionは同じ外側余白、同じ階層のcontrolは同じ高さを基本とする。

## 12. MOTION DIRECTION

### 必要なmotion

- loading中であることの穏やかなfeedback
- step / progressの状態遷移
- sidebar drawer、modal、collapseの位置関係を理解するtransition
- success・errorの出現時に視線を適切に誘導する短いfeedback
- hover / focus-visibleの即時反応

### 不要なmotion

- 常時動くAI sparkle、浮遊、pulse
- 意味のないgradient animation
- dashboard cardの自動スライド
- taskを遮る長いtransition
- loading中に内容の位置が大きく揺れる演出

Motionは状態理解を助ける場合だけ使い、`prefers-reduced-motion`では静的表現へ落とす。APIの完了やdisabled解除のタイミングは変更しない。

## 13. RESPONSIVE DIRECTION

Responsiveはdesktopの縮小版ではなく、画面幅ごとの仕事の優先順位として設計する。

### Mobileで最優先

- 現在の案件・現在のstep
- Required Attention
- Primary CTA
- input / confirm / reviewの次の操作
- loading / error / successの状態

### Mobileでsecondaryへ移すもの

- supporting metadata
- detailed KPI
- advanced diagnostics
- 長い説明と履歴の全量
- 管理者向け低頻度設定

Navigation drawer、sticky action area、1列flow、横スクロールtable、長文wrapを組み合わせる。重要なCTAやstatusを単に画面下へ押し込まない。既存test id、role、label、panel id、navigation stateは維持する。

## 14. AI VISUAL LANGUAGE

AI表現は「きらめき」ではなく、AIの関与と人の判断を追跡できる状態表現にする。

| 状態 | 表現 |
|---|---|
| AIが整理中 | 処理対象、進行stage、進行中ラベル、spinner / progress |
| AIが提案 | AI-assisted label、提案理由、source / provenanceの補助表示 |
| 人の確認が必要 | Required Attention、確認CTA、未確定status |
| 人が確定 | confirmed / reviewed status、確定時点または確定者のmetadata |
| 出力可能 | Quality Gate完了、available action、形式別CTA |
| 出力不可 | disabled状態と理由、必要な前提、retryまたは確認操作 |
| AIエラー | 何が失敗したか、利用者が取れる次の行動、retry |

AIが生成した内容と人が確定した内容を同じ色・同じbadgeで表さない。AI-assistedは補助的なlabelと状態説明を中心にし、sparkle、neon、強いgradient、ロボット人格に依存しない。

## 15. BEFORE → AFTER

1. 画面の中心が「機能の集合」から「案件を次に進める現在地」になる。
2. 大量のcardが、要約・要対応・詳細という明確な階層に整理される。
3. Proposal flowが長いフォームではなく、確認可能なstep railとして理解できる。
4. Primary CTAとSecondary CTAの強さが分かれ、次の操作を迷いにくくなる。
5. AIの存在感が装飾から、処理状態・提案状態・人の確認状態へ移る。
6. 不足情報、Review待ち、Quality Gate未完了が同じルールで理解できる。
7. 管理画面が巨大なaccordion一覧から、運用キューと優先順位のあるworkspaceになる。
8. 利用者画面は穏やかに、管理画面は密度高く、それでも同じ視覚言語で動作する。
9. desktopとmobileの情報順が揃い、mobileでもPrimary Actionが見失われない。
10. 見た目を変更しても、既存のtest id、ARIA、navigation、API、step、output契約が保たれる。

## 16. ANTI-PATTERNS

1. AIらしさをsparkle、neon、強いgradientだけで表現する。
2. すべての情報を同じ大きさ・同じcard・同じborderで表示する。
3. dashboardをKPI cardの羅列で終える。
4. 管理画面を巨大なaccordion一覧のまま装飾だけ変更する。
5. Primary CTAを画面ごとに複数置き、操作の優先順位を曖昧にする。
6. AI提案と人の確定を同じstatus表現にする。
7. warningとdangerを色だけで表し、具体的な次の行動を示さない。
8. desktop layoutをそのまま縮小し、mobileで横スクロールと縦長化だけを招く。
9. shadow、radius、浮遊surfaceを増やして階層不足を隠す。
10. visual redesignのためにtest id、accessible name、panel id、step、API条件を変更する。

## 17. REPRESENTATIVE SCREEN STRATEGY

全面変更ではなく、異なる情報構造を代表する4画面で方向性を検証する。

| 代表画面 | 検証すること | 選定理由 |
|---|---|---|
| User Home | 次の行動、最近の案件、空状態、navigation | 利用者の第一印象と全体の情報階層を確認できる |
| Proposal creation / Guided Flow | step、入力、AI整理、確認、loading、error、CTA | プロダクトの中核業務で、最も機能契約が密集している |
| Review / Quality Gate / Output | AI提案、人の確認、完了条件、出力可能性 | 信頼・責任・成果物到達の体験を検証できる |
| Admin Dashboard | readiness、要対応、状態、危険操作、管理密度 | 利用者画面との共通性と管理者特有の優先順位を検証できる |

この4画面でFoundation、surface、hierarchy、state、responsive、E2E契約の視覚的な適合性を確認してから、History、CRM、AI支援、Settings、各admin panelへ展開する。

## 18. HUMAN VISUAL REVIEW CRITERIA

スクリーンショットまたは実画面を人間が確認するとき、色の好みではなく以下で評価する。

| 評価軸 | 合格の観点 |
|---|---|
| Visual hierarchy | 視線の最初の位置、Primary Action、Required Attentionが自然に分かる |
| Readability | 日本語長文、数字、英数字、table、error messageを無理なく読める |
| Task clarity | 今どこにいて、何をすべきか、完了条件が分かる |
| Consistency | 同じ状態・操作・componentが同じルールで表現される |
| Density | 情報量に対して過密でも疎でもなく、画面目的に合う |
| Trust | AI提案、人の確認、未確定、出力可否を誤認しない |
| Professional quality | 営業・提案業務で顧客前後に使える落ち着きと精度がある |
| Generic AI signature | generic AI SaaSの装飾に見えず、Business Workbenchとして固有性がある |
| Responsive quality | mobileで優先順位が保たれ、操作・overflow・長文が破綻しない |

各項目を5段階で評価し、3未満が1つでもある場合は次画面へ展開しない。特にTask clarity、Trust、Responsive qualityはvisual polishより優先する。

## 19. CONTRACT PRESERVATION CHECKLIST

Foundation / conceptから実装へ移る際も、次を変更しない。

- `data-testid`
- role、aria-label、accessible name
- panel id、summary、navigation state
- `ProposalExperienceView`の値とrole filtering
- API call条件、single-flight、retry、response反映
- permission gating、Quality Gate、maintenance条件
- Proposal step順序とdownload/output behavior
- loading・disabled・error・successの発生条件

## 20. DESIGN CONCEPT DECISION

このConcept v1では、Visual Directionを「quietly capableなProposal Business Workbench」と確定する。次フェーズでは、この方向性をColor、Typography、Spacing、Radius、Shadow、Motion、BreakpointのFoundation Designへ落とし込む。ただし、Foundation Designでも具体的な既存CSS/TSX変更は別タスクとして扱う。

