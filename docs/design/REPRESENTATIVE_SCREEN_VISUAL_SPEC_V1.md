# Ready Crew Proposal AI Representative Screen Visual Design Spec v1

基準: UI Contract Freeze `2b7e18a` / `DESIGN_CONCEPT_V1.md` / `DESIGN_SYSTEM_FOUNDATION_V1.md` / `PRIMITIVE_COMPONENT_CONTRACT_V1.md`  
Direction: quietly capableなProposal Business Workbench  
対象: User Home、Proposal Creation / Guided Flow、Review / Quality Gate / Output、Admin Dashboard  
対象外: 既存TSX/CSS/testsの変更、画像生成、Production、Render/Vercel、Feature Flag、OpenAI API、Presentation Master、M30、renderer関連

この文書は実装前の画面レベルVisual / UX Specificationである。既存のdata-testid、role、aria、accessible name、panel id、navigation state、API call条件、permission gating、Proposal step order、loading/disabled/output behaviorは完全に維持する。

## 0. CURRENT CONTRACT RE-CHECK

| Screen | Current implementation | Current selectors / contract |
|---|---|---|
| User Home | `UserHomePanel`、AppShellの`experienceView === "home"` | `user-home-panel`、heading「今日は何をしますか？」、最近作成した提案書、ホームからのnavigation CTA |
| Proposal Creation | `GuidedFlow`、`StepNavigation`、`StepFooter`、AppShellの`experienceView === "new-proposal"` | `guided-flow`、`project-source-input`、guided step classes、ARIA labels、生成CTA、step order |
| Review / Quality / Output | GuidedFlowのStep 3〜5、`AiWorkspacePanel`、Quality Gate / output sections | `guided-quality-check`、Review/Quality/Outputのbutton names、loading/disabled、download unlock |
| Admin Dashboard | `AdminSection`、`RealOperationsDashboard`、各Admin*Panel | `admin-menu`、`admin-menu-panel`、`admin-*-panel`、summary、admin permission、table / diagnostic semantics |

### Frozen contract rule

Visual prototypeでは、既存DOMの意味を保ったまま、surface、spacing、typography、density、layout presentationだけを検証する。selectorや文言を新しい見た目に合わせて変更しない。

## A. USER HOME

### A1. PRIMARY JOB

ユーザーがログイン後すぐに「新しい提案書を作る」「作成途中を再開する」「最近の案件を確認する」のいずれかを迷わず選び、案件業務を開始すること。

ホームは分析dashboardではなく、今日の仕事への入口とする。最初にKPIを読ませず、次の行動と現在の作業状態を先に提示する。

### A2. INFORMATION PRIORITY

| Priority | 内容 | 表現 |
|---|---|---|
| P0 | 新しく提案書を作る、作成途中を再開する、現在のProposal state | page上部のPrimary work area、強いCTA、current state |
| P1 | 最近作成した提案書、直近案件、Quality GateやReviewの要対応 | 主作業直下のlist / attention row |
| P2 | 作成件数、削減時間、最近の補助情報 | compact summary、supporting section |
| P3 | 詳細分析、設定、低頻度の補助導線 | sidebar、secondary action、折りたたみ領域 |

### A3. PAGE ANATOMY — Desktop

1. App Header: product identity、workspace context、global actions
2. Sidebar: main navigation、active Home、role別item
3. Page Intro: 「今日は何をしますか？」と短い説明
4. Primary Work Area: 「新しく提案書を作る」と「作成途中を再開」
5. Current Work / Attention: 現在のProposal、Review待ち、Quality Gate状態
6. Recent Activity: 最近作成した提案書、resume action
7. Supporting Information: 作成数・削減時間等の補助情報
8. Secondary Actions: 履歴、分析・レポート、設定への導線

### A4. WIREFRAME DESCRIPTION — Desktop

```text
┌──────────────────────┬──────────────────────────────────────────────┐
│ AI営業秘書            │ workspace context                 global     │
│ 提案書作成ツール      ├──────────────────────────────────────────────┤
│                      │ 今日は何をしますか？                         │
│ ● ホーム              │ 提案業務を次の状態へ進めます                  │
│   提案書を作る        │                              [設定]          │
│   作成履歴            ├──────────────────────────────────────────────┤
│   分析・レポート      │ ┌──────────────────────┐ ┌──────────────────┐ │
│   設定                │ │ PRIMARY WORK        │ │ CURRENT WORK     │ │
│                      │ │ 新しく作る          │ │ 作成途中 / 要確認 │ │
│ ─ manager/admin ─    │ │ 案件情報を入力      │ │ 状態 + 次の操作   │ │
│                      │ │ [提案書を作る]      │ │ [再開する]        │ │
│                      │ └──────────────────────┘ └──────────────────┘ │
│                      ├──────────────────────────────────────────────┤
│                      │ 最近作成した提案書                           │
│                      │ 案件名 / 状態 / 更新日時             [履歴]   │
│                      │ ───────────────────────────────────────────── │
│                      │ recent row       status       [再開]          │
│                      ├──────────────────────────────────────────────┤
│                      │ 補助情報: 作成数 / 削減時間 / レポート         │
└──────────────────────┴──────────────────────────────────────────────┘
```

右側のCurrent Workは、常にcard化するのではなく、現在案件がある場合だけ独立した判断単位として表示する。何もない場合は、空状態とPrimary CTAを主作業領域に戻す。

### A5. VISUAL HIERARCHY

- Page title: 最初に読めるが、巨大なheroにはしない。
- Primary CTA: 「提案書を作る」。workspaceの主目的として一つだけ強調。
- Current state: Resume、Review待ち、Quality Gate等をCTAの近くに配置。
- Required attention: 未確認や要対応がある場合のみPrimary work直下に置く。
- Recent work: listとして扱い、card gridではなく行の比較性を優先。
- Metadata: 日時、担当、件数は弱いが読み取れるcontrastで配置。

### A6. SURFACE USAGE

- Page: app background。
- Primary Work Area: WorkspaceまたはPanel。案件開始という一つの業務目的を受け止める。
- Current Work: 現在案件・次の操作がある時だけCardまたはPanel。単なる装飾cardにしない。
- Recent Activity: Section + list/table。各案件を独立Cardにして壁を作らない。
- Supporting Information: Section内のcompact summary。KPI cardの羅列にしない。

### A7. RESPONSIVE BEHAVIOR

| Viewport | 残すもの | 移動・縮約 |
|---|---|---|
| Desktop | sidebar、page intro、primary workとcurrent workの並列、recent list | supporting infoは下段 |
| Tablet | sidebarは維持または既存collapse、primary workを優先 | current workをprimary直下へstack |
| Mobile | header、現在画面、Primary CTA、current state、required attention | drawer化、recentを縦list、supporting infoは後段または折りたたみ |

mobileでは「新しく作る」と「再開する」を最初に表示し、分析・設定・補助KPIは下へ移す。recent rowは横幅に合わせて案件名、status、主要actionを優先する。

### A8. BEFORE → AFTER

| CURRENT | TARGET |
|---|---|
| ホームが機能入口と情報表示の混在に見える | 今日の業務開始地点として明確に感じる |
| dashboard的な情報がPrimary actionと競合しうる | 最初の操作が「提案書を作る / 再開する」に収束する |
| recent contentがcardの集合になりやすい | listとして案件を比較・再開できる |
| empty時の次行動が弱い | 空状態でもPrimary CTAが自然に見える |
| supporting KPIが主役に見える | KPIは業務判断を支える補助情報になる |

## B. PROPOSAL CREATION / GUIDED FLOW

### B1. PRIMARY JOB

案件情報から、AI整理と人の確認を経て、提出可能な提案内容を作ること。入力欄を埋めることではなく、案件を次の確認可能な状態へ進めることが目的。

### B2. INFORMATION PRIORITY

| Priority | 内容 |
|---|---|
| P0 | 現在step、入力対象、次のPrimary CTA、生成状態 |
| P1 | AI整理結果、不足情報、確認対象、Review / Quality Gate状態 |
| P2 | helper、出典、補足説明、sample、draft notice |
| P3 | detail foldout、technical detail、拡張予定、advanced output detail |

### B3. PAGE ANATOMY — Desktop

1. App Header / Workspace Context
2. Guided Flow Top Bar: Proposal context、detail mode toggle
3. Stepper / Current State: 既存step順を維持
4. Main Work Panel: current stepのinputまたはreview
5. Required Attention Rail: 未入力、要確認、Quality Gate未完了
6. Supporting Detail: source、evidence、technical detail、foldout
7. Step Footer: current stepのPrimary / Secondary CTA

### B4. WIREFRAME DESCRIPTION — Desktop

```text
┌──────────────────────┬──────────────────────────────────────────────┐
│ sidebar               │ 提案書作成                 workspace context │
│                      ├──────────────────────────────────────────────┤
│                      │ ①入力 ─ ②AI整理 ─ ③確認 ─ ④チェック ─ ⑤出力 │
│                      │             current step / current state      │
│                      ├─────────────────────────────┬────────────────┤
│                      │ MAIN WORK PANEL             │ ATTENTION      │
│                      │ STEP title                  │ 要確認 2件     │
│                      │ label                       │ draft saved    │
│                      │ [textarea / fields]         │ 次の条件       │
│                      │ helper / validation         │                │
│                      │                             │                │
│                      │                             │                │
│                      ├─────────────────────────────┴────────────────┤
│                      │ supporting detail / 出典 / 詳細を開く          │
│                      ├──────────────────────────────────────────────┤
│                      │ [戻る/補助]                         [次へ/生成] │
└──────────────────────┴──────────────────────────────────────────────┘
```

Step 3以降はmain work panelを確認・編集対象へ切り替える。Semantic candidate、relationship、evidenceは、同じ画面内でAI proposal / human review / confirmedを追跡できる構造にする。対象外領域の詳細実装には踏み込まない。

### B5. VISUAL HIERARCHY

- Page / flow title: 「提案書を作る」。現在案件のcontextを添える。
- Stepper: current stepが最も強く、completeは確認済み、attentionは未完了、lockedは利用不可。
- Main work: current stepの入力・確認を最も広く取る。
- Required attention: main workの近くに置き、数と次の行動を示す。
- Primary CTA: footerのcurrent step action。画面上部とfooterで重複させない。
- Supporting info: 出典、helper、detail foldoutへ段階化。

### B6. SURFACE USAGE

- flow全体: Workspace。巨大なCardで包まない。
- 各step: Panel。step title、status、body、footerを持つ。
- individual semantic candidate / checklist item: Card。ただし各itemが独立した判断単位の場合のみ。
- input fields: Field group。fieldごとにCardを作らない。
- detail foldout: Advanced section。主作業と視覚的に分ける。

### B7. RESPONSIVE BEHAVIOR

- Desktop: stepperを上部に保ち、main workとattentionを2領域で配置。
- Tablet: attentionをmain work上部または直下へ移し、inputを1〜2列に調整。
- Mobile: stepperは横スクロールまたは短縮表示。ただしcurrent、complete、attentionは常に認識可能。
- Mobileの順序は current state → required attention → input/review → helper/detail → footer CTA。
- detail foldoutは初期閉鎖を基本とし、既存open条件は変更しない。
- long text、textarea、selectは横 clippingさせず、wrapと縦積みを優先。

### B8. STEPPER BEHAVIOR

| State | Visual | Interaction |
|---|---|---|
| current | active indicator、step title、現在目的 | 既存条件の範囲で操作 |
| complete | check、completed label、弱いaccent | 戻れる場合のみ既存条件で操作 |
| attention | warning icon +「要確認」 | attention対象と次の操作を提示 |
| locked | muted + lock / unavailable label | disabled条件を維持 |

番号・順序・accessible name・navigation stateは変更しない。Stepperはprogress decorationではなく、業務上の現在地を示す。

### B9. FORM RHYTHM

```text
Section title
  description / context
  label + required marker
  input / textarea / select
  helper or validation

次のfield（space-4〜space-5）
次のsection（space-6〜space-8）
footer action（sectionから明確に離す）
```

- labelはcontrolの直上、helperはcontrol直下。
- validationは入力の直下で、Required Attentionにも要約表示。
- section間はfield間より明確に広くする。
- Primary actionは最後の判断・生成位置に置く。
- sample、guide、draft noticeは主入力を邪魔しないSecondary領域に置く。

### B10. AI ASSISTED STATE

| State | 表現 |
|---|---|
| AIが整理中 | AI-processing label、対象、stage、spinner/progress。入力を必要範囲だけlock |
| AI提案済み | AI-assisted label、候補内容、出典/根拠、未確定status |
| 人の確認待ち | human-review label、要確認文言、確定・編集・不採用の操作 |
| 確認済み | confirmed label、check、確定後の操作状態 |

AI-assistedとbrand-primaryを同じ意味にしない。AIの提案は人の確定より弱い階層で表示し、sparkleやgradientを使って権威づけしない。

### B11. LONG FORM STRATEGY

- current stepをstickyまたは常時視認可能な上部stateとして残す。
- section titleと次の操作を近接させ、長いformを一枚のwallにしない。
- 必須入力、任意入力、AI整理結果、advanced detailをsurfaceとspacingで分ける。
- 現在step以外の情報をsummaryに縮約できる場合は折りたたむ。ただし既存表示条件は維持。
- footer CTAは画面下で見失わないようにするが、API条件とdisabled条件は変更しない。
- mobileでは入力→helper→validation→次のfieldの順を崩さない。

### B12. BEFORE → AFTER

| CURRENT | TARGET |
|---|---|
| step、input、detailが同じ強さで見える | 現在stepと次の操作が最初に分かる |
| AI整理と人の確認が近い表現になる | AI提案・要確認・確定済みを追跡できる |
| long formが縦長の入力集積になる | 一つずつ確認可能な業務stepに感じる |
| helperやdetailが主作業を押し下げる | supporting / advancedとして必要時に読める |
| CTAが複数領域に分散する | current stepのPrimary CTAに視線が収束する |

## C. REVIEW / QUALITY GATE / OUTPUT

### C1. PRIMARY JOB

AIが作成した提案内容を人が判断し、提出・出力可能な状態まで確実に通すこと。生成物を見ることだけでなく、未確認・修正・確定・出力可否を判断する画面。

### C2. INFORMATION PRIORITY

| Priority | 内容 |
|---|---|
| P0 | Needs review、現在のQuality Gate状態、次に必要な操作、出力可否 |
| P1 | AI proposal、issue found、human confirmed、checklist |
| P2 | 出典、詳細説明、quality score、履歴 |
| P3 | technical output detail、advanced diagnostics、内部情報 |

### C3. PAGE ANATOMY — Desktop

1. Page Header: 案件名、review state、主要action
2. Review Summary: AI proposal / Needs review / Human confirmedの集約
3. Required Attention: Issue found、未確認、品質不足
4. Quality Gate: checklistとcompletion state
5. Output Panel: PowerPoint / PDF等、可否と理由
6. Supporting Detail: score、source、review history
7. Secondary Actions: 再確認、履歴、補助出力

### C4. WIREFRAME DESCRIPTION — Desktop

```text
┌──────────────────────┬──────────────────────────────────────────────┐
│ sidebar               │ 案件名 / Review                         [戻る]│
│                      ├──────────────────────────────────────────────┤
│                      │ REVIEW SUMMARY                                │
│                      │ AI proposal   要確認 3件   確認済み 5件         │
│                      ├─────────────────────────────┬────────────────┤
│                      │ PROPOSAL REVIEW              │ REQUIRED       │
│                      │ proposal item                │ ATTENTION      │
│                      │ AIによる候補                 │ Issue found    │
│                      │ [確認] [編集] [不採用]       │ 未確認項目     │
│                      │ 人の確認 / 根拠              │ 次の操作       │
│                      ├─────────────────────────────┴────────────────┤
│                      │ QUALITY GATE                                  │
│                      │ ✓ 確認項目   ○ 人の確認   ○ 提出前チェック       │
│                      │                                      [完了する] │
│                      ├──────────────────────────────────────────────┤
│                      │ OUTPUT                                        │
│                      │ PowerPoint [利用可/ロック理由]  PDF [状態]       │
│                      │                              [出力方法を選ぶ]   │
└──────────────────────┴──────────────────────────────────────────────┘
```

### C5. VISUAL HIERARCHY

- Review stateはpage header直下に常時表示。
- Needs reviewはwarning toneと明確な文言で表現するが、画面全体をdanger色にしない。
- Human confirmedはsuccess/confirmedとして、AI proposalより強い確定状態にする。
- Issue foundはRequired Attention内で件数・優先度・修正actionを示す。
- Quality GateはReviewの後、Outputの前に配置。
- OutputはQuality Gateと隣接させ、ロック理由を同一領域に置く。

### C6. SURFACE USAGE

- Review全体: Workspace。
- Review summary: Panel。状態の集約と進行を示す。
- 各review item: Card。item単位で確認・編集・不採用の判断がある場合のみ。
- Quality Gate: Panel。checklistとcompletion actionを持つ。
- Output: Panel。形式別optionはCardではなく選択可能なoption rowとして扱う。
- score・source・history: supporting sectionまたはfoldout。

### C7. RESPONSIVE BEHAVIOR

- Desktop: review contentとattentionを並列。Quality GateとOutputは縦の業務順。
- Tablet: attentionをreview summary直下へ移し、review itemを1列にする。
- Mobile: review state → attention → current item → Quality Gate → Outputの順。
- Output actionは画面最下部まで埋もれないよう、既存条件の範囲でsticky footer候補。
- 長いproposal textはwrapし、horizontal clippingさせない。
- output optionは横に詰めず、形式・状態・理由・actionの順に縦積みする。

### C8. REVIEW STATE MODEL

```text
AI proposal
    ↓ 人の確認が必要
Needs review
    ├─ Issue found → 修正 / 再確認
    └─ Human confirmed
             ↓ Quality Gate
       Ready for output
```

| State | Visual relation | Action |
|---|---|---|
| AI proposal | AI-assisted label、候補表示、弱いsurface | review action |
| Needs review | human-review、attention indicator | 確認・編集・不採用 |
| Human confirmed | confirmed、check、確定者/metadata | 次項目またはGateへ |
| Issue found | warning/danger severityを区別、理由を表示 | 修正・再試行・確認 |
| Ready for output | success/confirmed、Quality Gate完了 | output action |

### C9. QUALITY GATE HIERARCHY

Quality Gateは警告boxではなく、提出責任を確認する業務Panelとして扱う。

- Header: Quality Gateの目的と現在状態
- Checklist: 完了、未完了、要確認を行単位で表示
- Attention summary: 未完了数と影響
- Completion action: 既存の「提出前チェックを完了する」等のaccessible nameを維持
- Completed state: 完了時点と出力可否を明示
- Admin bypass: 通常完了と視覚的に区別し、権限条件は変更しない

### C10. OUTPUT LOCK / UNLOCK

形式ごとに次を同じ順序で表示する。

1. Output format
2. Current availability
3. Lock reasonまたは前提
4. Primary action / retry

Locked outputは単にgray disabledにせず、「何が必要か」を近接表示する。Unlocked outputはQuality Gate完了と混同しない。PowerPoint / PDF等の既存出力条件・download behaviorは変更しない。

### C11. REQUIRED ATTENTION

- Required Attentionは画面上部またはreview contentの近くに置く。
- 件数、優先度、対象、次の操作を示す。
- warningとdangerを混在させず、継続可能な不足と継続不能なエラーを分ける。
- 全項目を赤くせず、最優先1〜3件を先に見せる。
- issueがない場合はsuccess/neutralの短いsummaryに置き換え、空白だけを残さない。

### C12. BEFORE → AFTER

| CURRENT | TARGET |
|---|---|
| Review、Quality Gate、Outputが連続する情報群に見える | 判断→確認→出力の業務順が明確になる |
| warningが多く、何から直すか分かりにくい | Required Attentionに優先順位と次 actionがある |
| AI proposalとconfirmedが近い見た目になる | 状態の責任境界が明確になる |
| Quality Gateが単独のchecklistに見える | 提出判断と出力unlockの中心になる |
| output lockがdisabled buttonだけに見える | 形式、可否、理由、前提を即座に理解できる |

## D. ADMIN DASHBOARD

### D1. PRIMARY JOB

管理者が、今日対応すべき運用・品質・権限・システム状態を短時間で把握し、必要なpanelへ直接進むこと。

Admin Dashboardは全機能を見せる場所ではなく、運用上の判断と次のactionをまとめる入口とする。

### D2. INFORMATION PRIORITY

| Priority | 内容 |
|---|---|
| P0 | Needs Attention、system readiness、権限/品質/停止に関する重大状態 |
| P1 | Daily Operations、利用状況、品質、ユーザー管理、監査 |
| P2 | AI / Integrations、release、trial report、改善分析 |
| P3 | Prompt Studio、Learning、Knowledge、technical diagnostics |

### D3. PAGE ANATOMY — Desktop

1. Admin Page Header: 管理コンソール、scope、更新情報
2. Daily Operations: 今日のreadinessと要対応summary
3. Needs Attention: alert、failed、pending、riskの優先queue
4. Quality & Usage: quality、usage、feedback、analytics
5. Users & Permissions: users、Workspace、permission
6. AI & Integrations: AI設定、external integrations、release
7. System Health: health、diagnostics、operation readiness
8. Advanced / Diagnostics: logs、Prompt、Learning、Knowledge
9. Danger Zone: delete、bypass、maintenance、retention

### D4. WIREFRAME DESCRIPTION — Desktop

```text
┌──────────────────────┬──────────────────────────────────────────────┐
│ sidebar               │ 管理コンソール             更新 / scope       │
│                      ├──────────────────────────────────────────────┤
│                      │ DAILY OPERATIONS                             │
│                      │ system ready   users   quality   logs         │
│                      ├─────────────────────────────┬────────────────┤
│                      │ NEEDS ATTENTION              │ QUICK ACTIONS  │
│                      │ 要対応 queue                  │ ユーザー管理   │
│                      │ severity / owner / next      │ 利用状況       │
│                      │ [対象panelを開く]             │ 監査ログ       │
│                      ├─────────────────────────────┴────────────────┤
│                      │ QUALITY & USAGE                               │
│                      │ usage trend / feedback / quality summary       │
│                      ├──────────────────────────────┬───────────────┤
│                      │ USERS & PERMISSIONS           │ AI / SYSTEM    │
│                      │ user summary / workspace      │ health / links  │
│                      ├──────────────────────────────┴───────────────┤
│                      │ ADVANCED / DIAGNOSTICS  [必要時に開く]          │
│                      │ DANGER ZONE             [確認付き操作]          │
└──────────────────────┴──────────────────────────────────────────────┘
```

### D5. VISUAL HIERARCHY

- Admin page titleは明確だが、user-facingのheroのように大きくしない。
- Readiness / Needs Attentionが最上位。低頻度の技術panelを先頭に置かない。
- 要対応rowはseverity、status、対象、actionの順で読む。
- Normal状態はneutral、対応必要な状態だけwarning/dangerで強調。
- 高度機能は見えるが、通常運用のprimary actionと競合しない。
- Danger Zoneは通常のQuick Actionsから隔離する。

### D6. SURFACE USAGE

- Page: admin background。
- Daily Operations: Workspace / Panel。今日見るべき集約。
- Needs Attention: Panel + priority list。各issueが独立判断単位ならCard。
- Quality & Usage: Section + table / compact summary。card gridにしない。
- Users & Permissions: Panel + table。
- AI & Integrations / System Health: Panel。状態とactionを近接。
- Advanced: Disclosure / Panel。技術詳細を常時展開しない。
- Danger Zone: 明確な独立Panel。surface・border・confirmationで通常操作と分離。

### D7. RESPONSIVE BEHAVIOR

- Desktop: readinessとattentionを上部、data-heavy領域を下部。
- Tablet: attentionを先頭に残し、Quality / Users / Systemを縦積み。
- Mobile: page title → Needs Attention → Daily readiness → quick actions → tables/detailsの順。
- 低頻度Advanced panelは後段へ移動。panel idと既存details契約は維持。
- tableは重要列とrow actionを優先し、横スクロールまたは詳細化する。
- Danger Zoneは通常のquick actionに混ぜず、最下部または明確な隔離領域へ配置。

### D8. ADMIN INFORMATION ARCHITECTURE

既存panelを機能変更せず、視覚的なカテゴリとして次のように整理する。

| Conceptual category | 現行機能の対応 |
|---|---|
| Daily Operations | Admin readiness、Health、Operation Readiness |
| Needs Attention | feedback、pilot issue、errors、release pending、quality alerts |
| Quality & Usage | Product Analytics、Usage Dashboard、Improvement Dashboard、Pilot Dashboard |
| Users & Permissions | Admin Users、Workspace / Permission Settings |
| AI & Integrations | Beautiful.ai / OpenAI diagnostics、External Integrations、Sales Assistant |
| System Health | HealthStatus、SystemDiagnostics、Queue Monitor |
| Advanced / Diagnostics | Prompt Studio、Learning、Knowledge、audit detail |
| Danger Zone | user delete、bypass、maintenance、retentionなどの既存危険操作 |

これはvisual groupingであり、既存panel id、permission、API、functionを変更するものではない。

### D9. DENSITY

- AdminはCompact density。ただしbody 14px未満にしない。
- table rowは40〜48px、cell paddingは8px 12pxを基準。
- panel paddingは16px、section gapは20〜24px。
- status、label、focus ring、danger actionはcomfortableと同等の視認性を保つ。
- 数字、status、row actionのcolumn位置を固定し、比較を容易にする。
- long error、URL、technical identifierはwrapまたは専用detailに逃がす。

### D10. ADMIN PRIORITY MODEL

| Axis | 強くする条件 | 視覚 |
|---|---|---|
| Frequency | 毎日・毎回見る | 上部、常時表示、短いsummary |
| Importance | 利用継続・品質・権限に影響 | strong heading、action近接 |
| Risk | 削除・停止・bypass・retention | danger separation、confirm、説明 |
| State | failed / pending / blocked | warning/danger + label + next action |

同じ状態でも、頻度が低いtechnical detailをDaily Operationsと同じ強さで表示しない。

### D11. ACCORDION REDUCTION STRATEGY

既存`details`構造は機能契約として維持するが、視覚上は次の原則で巨大accordion感を抑える。

- カテゴリ間にsection rhythmとcategory headerを置く。
- 常に見るreadiness / attentionはsummaryではなく上部の集約Panelで示す。
- `details`はAdvanced / low-frequency / large data blockに限定して見せる。
- 同じ見た目のsummaryを連続させず、カテゴリ・状態・件数をsummaryに反映。
- 開閉状態、summary text、panel id、E2E locatorは変更しない。
- panel内部のCard乱用を避け、table・list・status rowを使う。
- open時にページ全体を押し下げすぎないよう、scroll・layoutを設計する。

### D12. BEFORE → AFTER

| CURRENT | TARGET |
|---|---|
| 管理機能が同じ強さのaccordionに並ぶ | Daily / Attention / Advancedの優先順位が分かる |
| readiness、diagnostics、settingsが混在 | 今日の運用判断が先に読める |
| cardとtableが画面ごとにばらつく | compactな同一primitiveで比較できる |
| warningが多く、重大度が読み取りづらい | 状態・頻度・リスクで表示強度が変わる |
| Danger操作が通常actionに近い | 危険操作が明確に隔離される |

## CROSS-SCREEN SYSTEM

### 1. Page Header pattern

```text
eyebrow (必要な場合のみ)
Page title
短いdescription
current context / metadata
page-level actions（Primaryは原則1つ）
```

Page titleは日本語業務目的、eyebrowは分類やphaseが必要な場合だけ。HeaderとPage Headerを競合させない。

### 2. Section rhythm

- Page padding: desktop 24〜32px、mobile 16px
- section gap: comfortable 32px、compact 20〜24px
- panel padding: comfortable 24px、compact 16px
- field gap: comfortable 20px、compact 12px
- required attentionは関連する主作業の直前または直後に置く

### 3. Primary CTA placement

- page-level primary: Page Header右側またはPrimary Work Area。
- flow-level primary: current stepのfooter。
- review/output primary: current stateとactionが同じpanel内。
- admin primary: Needs Attentionの対象panel actionまたはDaily Operationsの主要操作。
- 同じ画面に同じ強さのPrimary CTAを複数置かない。

### 4. Status placement

- page-level state: Page Header直下。
- panel-level state: Panel header。
- item-level state: itemのtoplineまたはlabel近接。
- transient loading/success/error: 実行対象の近く。
- statusを画面右上や遠いbannerだけに置かない。

### 5. Required Attention placement

- User Home: Current Workの直下。
- Guided Flow: current stepとinput/reviewの近く。
- Review: summary直下、Quality Gateの前。
- Admin: page上部のNeeds Attention queue。

### 6. Empty / Loading / Error placement

- Empty: 対象Panel / Section内。解消CTAがある場合のみCTA。
- Loading: 同じ領域内でSkeleton / Spinner / Progressを使い分ける。
- Error: 対象操作の近くに原因・影響・retryを置く。
- page全体を覆うoverlayは、既存のblocking条件がある場合に限定。

### 7. Workspace context placement

HeaderまたはHeader直下に固定し、案件・Organization・Workspaceのscopeを常に認識できるようにする。contextをmain contentの中へ毎回重複表示しない。

### 8. Desktop content max-width

- App shell: 既存のwide workspace幅を尊重。
- reading content: おおむね720〜880px相当で長文を制限。
- data-heavy admin: 100% workspace幅を使用可能。
- Guided flow: main workを広く、attentionを固定的な補助幅で配置。
- 具体値の実装はFoundation tokenに接続し、既存layoutのbehaviorを先に確認する。

### 9. Comfortable / Compact density rules

User Home、Guided Flow、Reviewはcomfortable。Admin Dashboard、logs、analyticsはcompact。ただしButton、focus、status、error、touch targetのsemantic contractは共通。

### 10. User / Admin visual continuity

- 同じsemantic color、type hierarchy、button、field、statusを使う。
- userはcomfortable、adminはcompact。
- userは「次の行動」、adminは「要対応と状態」を上位に置く。
- 片方だけ別brand、別radius、別status vocabularyにしない。

## VISUAL DIFFERENTIATION

| Concept | 色以外の区別 | 主な位置 |
|---|---|---|
| Navigation | sidebar structure、active indicator、icon + label、`aria-current` | App Shell |
| Main Work Area | 最大のcontent width、comfortable spacing、clear heading | Workspace center |
| Supporting Information | 弱いsurface、compact type、secondary position | main workの下/横 |
| AI Suggestion | AI-assisted label、source、候補status、提案理由 | review item |
| Human Review | human-review label、確認CTA、attention indicator | review / Quality Gate |
| Confirmed Information | confirmed label、check、確定metadata、操作制限 | item / summary |
| Required Attention | warning/danger icon、件数、優先度、next action | main work近接 |
| System Status | status summary、timestamp、health label、technical detailの分離 | header / admin |
| Danger Action | isolated zone、説明、confirmation、danger action | Admin Danger Zone / Confirm Dialog |

色、icon、label、border、位置、操作のうち最低2つを組み合わせる。色だけでstatusを判断させない。

## HUMAN VISUAL REVIEW SCORECARD

実装後のscreenshot reviewで各項目100点評価する。

| Criterion | 100点の状態 |
|---|---|
| Visual Hierarchy | P0/P1/P2/P3の順に視線が自然に進む |
| Task Clarity | 今どこにいて、何をすべきか、完了条件が明確 |
| Information Density | 画面目的に対して過密でも疎でもない |
| Typography | 日本語長文、数字、英数字、tableが読みやすい |
| Spacing Rhythm | page / section / panel / fieldの間隔が一貫 |
| Component Consistency | 同じsemantic roleが同じvisual grammarで表示 |
| Status Clarity | 色以外の手掛かりでもstateが分かる |
| AI/Human Distinction | AI提案、Review、confirmedを誤認しない |
| Trust / Professional Quality | 顧客前後で使える落ち着き・精度・説明責任 |
| Responsive Quality | mobileで優先順位、wrap、overflow、操作が破綻しない |
| Generic AI Signature | AI SaaS templateではなくProposal Workbenchに見える |

Generic AI Signatureは「genericさ」を0点理想として採点し、20点以上をFAIL候補とする。他の項目は90点以上を目標とする。

## FAIL GATES

- No primary CTA ambiguity
- No card wall
- No excessive accordion feel
- No fake AI decoration
- No status-by-color-only
- No horizontal clipping
- No text collision
- No hidden required action

いずれかに該当する場合、色や装飾の完成度にかかわらず代表画面のvisual approvalを保留する。

## DESIGN REVIEW ORDER

1. User HomeでPage Header、Primary Work、empty/recent hierarchyを確認。
2. Guided Flowでstep、form rhythm、AI/Human distinction、mobile sequenceを確認。
3. Review / Quality / Outputでtrust、state、lock/unlock、required attentionを確認。
4. Admin Dashboardでcompact density、priority、accordion reduction、danger separationを確認。
5. 4画面共通でcolor、type、spacing、surface、responsive、E2E contractを突合。

この順序で、全画面を一気に変更せず、代表画面の設計品質を確認してから展開する。

