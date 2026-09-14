# Ready Crew Proposal AI Primitive Component Contract v1

基準: `DESIGN_SYSTEM_MIGRATION_INVENTORY.md` / `DESIGN_CONCEPT_V1.md` / `DESIGN_SYSTEM_FOUNDATION_V1.md`  
Product direction: quietly capableなProposal Business Workbench  
Scope: component contract策定のみ  
対象外: 既存TSX/CSS/testsの変更、Production、Render/Vercel、Feature Flag、OpenAI API、Presentation Master、M30、renderer関連

この文書は、分散したUIをひとつのDesign Systemへ段階的に統合するための契約である。Primitiveのsemantic responsibilityとvisual appearanceを分離し、UI Contract LEVEL 1を完全に維持する。

## 0. GLOBAL CONTRACT

- `data-testid`、role、aria-label、accessible name、panel idは変更しない。
- navigation state、API call条件、permission gating、Proposal step orderを変更しない。
- loading / disabled / retry / success / errorの発火条件と出力behaviorを変更しない。
- existing classはmigration完了までcompatibility aliasとして保持する。
- user / manager / adminは同じPrimitiveを使い、density presetで調整する。
- variantはsemantic differenceがある場合だけ追加する。見た目の好みで増やさない。
- componentは「何を意味するか」と「どう見えるか」を別契約にする。

## 1. BUTTON CONTRACT

### Variants

| Variant | Semantic purpose | 使用条件 | 禁止用途 |
|---|---|---|---|
| Primary | 現在の主目的を完了させる | 1画面の主業務CTA。生成、確認、完了、出力 | 同一画面で複数を同じ強さで乱立 |
| Secondary | Primaryを補助する安全な操作 | 戻る、再読込、保存、別経路、補助出力 | Primaryの代替を大量に並べる |
| Tertiary / Text | 低優先度・局所操作 | 詳細表示、キャンセル、補助リンク、行内操作 | destructive action、重要な完了操作 |
| Danger | 破壊的・停止・不可逆操作 | 削除、bypass、maintenance、retention等 | 通常の操作や単なる注意表示 |
| Icon | アイコンで意味が明確な局所操作 | close、refresh、前後移動、compact row action | アイコンだけでは意味が曖昧な主要操作 |

### Size / density

| Size | Comfortable | Compact | 用途 |
|---|---:|---:|---|
| compact | visual 36px / hit 44px | visual 36px / hit 44px | table、toolbar、行内操作 |
| default | 44px | 40〜44px / hit 44px | 標準操作 |
| large | 52px | 原則使用しない | Proposal生成、Quality Gate完了等の主CTA |

Foundationのcontrol sizeと一致させる。horizontal paddingはcompact 12px、default 16px、large 20pxを基準とする。

### State contract

- default: variant固有のsemantic surface。
- hover: hover tokenと軽微なborder/elevation変化。
- focus: 2px以上のfocus indicator。outlineを消さない。
- active: pressedまたはnavigation/actionの実行中状態。視覚だけで済ませない。
- disabled: native `disabled`を優先。理由が必要な場合は近接helper/Statusで説明。
- loading: `isLoading`または既存loading条件を保持し、labelまたはaccessible nameを失わない。二重送信を防止。
- success / errorはbutton自体のvariantにせず、実行後のStatus / Alertで表現する。

### Icon / accessible name

- iconはleadingを基本とし、downloadやexternal actionはtrailingも許可。
- icon-onlyは`aria-label`必須。visible textがあるbuttonのiconはdecorative扱い。
- accessible nameは既存E2EとUI Contract Freezeに従い変更しない。
- focus ringはicon-onlyでも44px hit area全体に表示する。

### Primary CTA rule

- 1画面1主目的、Primary CTAは原則1つ。
- Proposal flowではstepの現在目的に対して1つ。補助生成・別出力はSecondary以下。
- adminでは一覧の各row actionにPrimaryを使わず、画面全体の主目的だけに使う。
- disabled Primaryには、可能な限り近接した未完了理由を示す。ただし条件は変更しない。

### Legacy mapping

| Legacy | Contract mapping |
|---|---|
| `.primary-button` | Button / Primary |
| `.secondary-button` | Button / Secondary |
| `.danger-button`、`.secondary-button.danger` | Button / Danger |
| `.text-button`、`.secondary-action` | Button / Tertiary |
| `.icon-button` | IconButton / Icon |

## 2. FORM CONTROL CONTRACT

### Shared structure

```text
Field
 ├─ label (+ required marker)
 ├─ control: Input / Textarea / Select / Checkbox
 ├─ helper (optional)
 ├─ character count (optional)
 └─ error or success message (optional)
```

- placeholderはlabelの代わりにしない。
- labelとcontrolは明示的に関連付ける。
- requiredは`required` semanticsとvisible markerを一致させる。
- errorは対象controlの近くに置き、色だけで示さない。
- successは入力が確定・検証済みの場合だけ使い、単なる入力済みには使わない。
- read-onlyは値を読めるが変更できない状態。disabledとは意味を分ける。
- loadingは値取得・保存・候補生成中の状態を示し、必要な範囲だけdisabledにする。

### Control responsibilities

| Control | 責務 | 主なstate |
|---|---|---|
| Field | label、helper、error、required、layoutを統合 | default、error、success、disabled |
| Input | 1行の短い値、名前、URL、検索 | focus、invalid、read-only、loading |
| Textarea | 長文、案件情報、メモ、コメント | focus、character count、invalid、loading |
| Select | 定義済み選択肢、workspace、relation endpoint | selected、disabled、loading、error |
| Checkbox | 独立したyes/no、目的、checklist | checked、indeterminate、disabled |

### Prefix / suffix / character count

- prefix / suffixは値の意味を補助するものに限定し、labelの代わりにしない。
- prefix / suffixがある場合もkeyboard focus領域とerror associationを壊さない。
- character countは制限がある入力だけに表示し、常時表示で認知負荷を増やさない。
- countは「現在 / 最大」のように読み上げ可能なtextで提供する。

### Field state rules

- disabled: permission、maintenance、loading等の既存条件を尊重。
- read-only: review済み値、context値等、確認は必要だが編集不要な情報に使用。
- error: 原因、対象、修正方法をhelperまたはinline messageで示す。
- success: server/APIまたは明確なvalidation結果に基づく場合のみ。
- focus: borderだけでなくfocus ringを使う。
- placeholderは補助例。重要な説明をplaceholderに置かない。

## 3. CARD CONTRACT

Cardは独立した判断単位を囲う場合だけ使う。「何でも囲う箱」にはしない。

### Allowed variants

| Variant | Semantic condition | 例 |
|---|---|---|
| standard | 独立した要約・KPI・情報単位 | Recent proposal、metric、summary |
| interactive | クリックまたは選択可能な単位 | nav-like choice、selectable item |
| selected | 現在選択中・activeな単位 | selected template、selected option |
| attention | 要確認・未完了・リスクを含む単位 | missing info、review waiting |

不要なbrand、gradient、elevated、large、small variantは追加しない。visual差だけでvariantを増やす場合は不採用とする。

### Card vs Panel vs Section

- Card: 独立した判断単位。複数並べても各単位が意味を持つ。
- Panel: 業務領域・作業領域。header、body、action、footerを持ち、継続的な作業を受け止める。
- Section: Page内の情報階層。必ずしも背景・border・shadowを持たず、見出しと余白で区切る。
- Page / WorkspaceをCardで包まない。
- Card内に無意味なCardを入れ子にしない。

## 4. PANEL CONTRACT

### Standard structure

```text
Panel
 ├─ header
 │   ├─ title
 │   ├─ description (optional)
 │   ├─ status (optional)
 │   └─ actions (optional)
 ├─ body
 └─ footer (optional)
```

- headerはpanelの業務目的を示す。
- statusはpanel全体の状態。rowやfieldの状態はbody内で管理する。
- actionsはpanel目的に直結するものだけ。global navigationを入れない。
- footerは次step、保存、確認、出力など、bodyの結果に対する操作に限定。
- bodyはフォーム、table、checklist、summary等の業務内容を持つ。
- Disclosure panelは開閉可能でも、panel id、summary、open条件、ARIAを維持する。

### Panel boundary

- 長時間作業・複数要素・状態遷移がある場合はPanel。
- 1つの値、要約、判断結果はCard。
- 関連要素をsectionとしてまとめられる場合、PanelやCardを追加しない。
- 管理画面の高度情報はPanelまたはDisclosureへ集約し、Cardを大量に追加しない。

## 5. SECTION HEADER CONTRACT

```text
SectionHeader
 ├─ eyebrow (optional)
 ├─ title (required)
 ├─ description (optional)
 ├─ metadata (optional)
 └─ actions (optional)
```

- titleは必須。ページ内で何を判断・操作するかを日本語で示す。
- eyebrowは分類、phase、短いcontextを示す場合だけ。全sectionに付けない。
- eyebrowはtitleの代替にしない。英語ラベルを増やして情報階層を作らない。
- descriptionは操作に必要な補足だけ。長文はbodyへ移す。
- metadataは日時、担当、件数、scope等、titleを補助する情報に限定。
- actionsはsectionのPrimary/Secondary操作。ページglobal actionを混在させない。

## 6. BADGE / STATUS CONTRACT

### Boundary

- Badge: 短い属性・分類・filter・状態ラベル。単体では詳細説明や操作を担わない。
- Status: 現在の状態、進行、確認要否、結果を伝える。ラベル・icon・説明またはactionを伴える。
- Alert: 利用者の注意や行動が必要なメッセージ。Severityと次の行動を持つ。

### Status vocabulary

| Status | Semantic rule | 非色の表現 |
|---|---|---|
| neutral | 未分類、情報のみ、変化なし | neutral label |
| info | 補足、non-blocking | info icon +説明 |
| success | 完了、利用可能、成功 | check icon +完了文言 |
| warning | 要確認、期限、不足 | warning icon +要確認 +次 action |
| danger | 失敗、停止、破壊的操作 | alert icon +原因 +確認/再試行 |
| AI-assisted | AIが整理・提案に関与 | AI-assisted label +対象/根拠 |
| AI-processing | AIが処理中 | processing label +stage/progress |
| human-review | 人の確認が必要 | review label +確認CTA |
| confirmed | 人が確認・確定済み | confirmed label +check |

AI-assistedはbrand-primaryの別名ではない。AI-processingはloading中だけ、confirmedは人の確定後だけ使用する。

## 7. ALERT / INLINE MESSAGE CONTRACT

| Type | 使う条件 | 構造 |
|---|---|---|
| info | 知っておくと役立つが作業を阻害しない | icon +短い説明 |
| success | 操作や保存が完了した | icon +完了内容 +必要なら次 action |
| warning | 不足・要確認・期限・部分的リスク | icon +影響 +修正/確認 action |
| danger | 失敗、停止、破壊的操作、継続不能 | icon +原因 +retry/restore/confirm |

- Alertはpage、panel、formなどの作業を中断または注意喚起する場合に使う。
- Statusは状態を伝える場合に使い、毎回大きなalertにしない。
- helper textは入力を助ける補足、format、単位、制約に限定する。
- errorは`role=alert`、non-blocking statusは`role=status`等の既存semanticsを維持。
- toastは将来追加する場合も、重要なerror・confirmationをtoastだけに閉じ込めない。

## 8. EMPTY STATE CONTRACT

```text
EmptyState
 ├─ icon / illustration (optional)
 ├─ title (required)
 ├─ description (required)
 ├─ primary action (optional)
 └─ secondary action (optional)
```

- titleは「何がないか」、descriptionは「次にどうするか」を明確にする。
- Primary actionは空状態を解消する明確な操作がある場合だけ。
- Secondary actionは別の安全な経路がある場合だけ。
- 単なる「まだありません」に無理にCTAを付けない。
- illustration/iconは意味補助に限定し、AI装飾や大きな空白の埋め合わせにしない。
- loading中はEmptyStateを出さず、loading contractと混同しない。

## 9. LOADING CONTRACT

| Primitive | 使用条件 | 表現 |
|---|---|---|
| Skeleton | page / panelのlayoutが分かり、待機中も構造を見せられる | 実コンテンツに近いplaceholder |
| Spinner | 短い局所処理、button、refresh、small region | spinner +何を待つかのlabel |
| Progress | 進捗値または処理stageが説明可能 | determinate値または意味のあるstage |

### AI processing rules

- 何を処理しているか: 対象とstageを表示。
- 待つ必要があるか: 操作継続可能か、画面を離れてよいかを示す。
- 操作可能か: 対象controlのdisabled / busyを既存条件どおり表現。
- progress値が実際に計測できない場合、fake percentageを表示しない。indeterminateまたはstage表示を使う。
- loading中にlayoutを大きく移動させない。
- retryは失敗後だけ表示し、API call条件を変更しない。
- Skeletonは空状態やerrorの代替にしない。

## 10. MODAL / CONFIRM DIALOG CONTRACT

### Boundary

- Modal: 作業文脈を一時的に遮って、入力・閲覧・選択を行うcontainer。
- Confirm Dialog: destructive、unsaved changes、重要な確定など、明示的な判断を求める短いModal。

### Usage rules

| Situation | Component | Rule |
|---|---|---|
| destructive action | Confirm Dialog | 対象、影響、取消可能性、確定actionを明示 |
| unsaved changes | Confirm Dialog | 失う内容と戻る/破棄の選択を明示 |
| important confirmation | Confirm Dialog | Quality Gate、提出、確定等に限定 |
| informational content | Modalまたはinline | 単に読ませるだけならModalで遮らない |

- 既存の`role=dialog`、`aria-modal=true`、accessible name、close behaviorを維持。
- modal内のPrimaryは確定・続行、Secondaryはcancel/back、Dangerは破棄・停止に限定。
- backdrop clickやEscapeの挙動は既存契約を確認してから実装する。
- 重要な業務内容をmodalだけに閉じ込めず、主画面から現在stateを把握できるようにする。

## 11. DRAWER CONTRACT

### Navigation drawer

- mobile sidebar、menu、画面移動に使用。
- navigation item、active state、role filter、open/collapse、backdrop契約を維持。
- desktopでは常設sidebarとのvisual counterpartとして扱う。

### Contextual drawer

- 現在の案件やrowの補足詳細、secondary toolsに使用。
- 主作業の次の一手、Quality Gate、重要なerrorをdrawerだけに置かない。
- close、back、focus、scroll boundaryを明示する。
- drawerはmodalより軽い補助領域だが、overlay layerとしての視認性を持つ。

## 12. TABLE CONTRACT

- header: column label、unit、sort/filter semanticsを明確にする。
- row: 1行1record。row全体をclickableにする場合はaccessible nameとrow actionを分離。
- numeric: 右揃えまたは桁を比較しやすいalignment。単位を同じ位置に揃える。
- status: Status/Badgeと文言を併用。色だけで判定させない。
- row action: row内で最も安全な操作を優先し、Dangerは独立・確認付き。
- empty: tableを空の枠だけにせず、EmptyStateをtable contextに合わせる。
- loading: row skeletonまたはtable-level progress。Emptyと混同しない。
- horizontal overflow: desktopでは幅を保ち、mobileでは重要列を優先して横スクロールまたは詳細化する。
- compact density: row heightとcell paddingを縮めるが、focusとtouch targetを削らない。
- header、column、row action、sort state、table scrollの既存E2E契約を維持する。

## 13. TABS CONTRACT

- Tabsは同一目的・同一階層・同一context内の表示切替に使用する。
- 例: かんたん入力 / 詳細入力、同一workspace内のsubview。
- Navigationは別画面・別業務領域への移動。sidebarやmain navigationをTabsで代用しない。
- 深い階層navigation、permission別の画面群、長いworkflowをTabsに押し込まない。
- selected tab、keyboard、`aria-selected`、tabpanel associationを設計する。
- tabを増やしすぎず、4〜6個を目安にする。超える場合はinformation architectureを再検討する。

## 14. STEPPER CONTRACT

Proposal Flowの既存step orderをそのまま契約とする。

| State | 表現 | 操作 |
|---|---|---|
| current | 強いindicator、step title、現在の目的 | 現stepの操作を許可 |
| complete | check、completed label | 必要な場合のみ戻れる |
| attention | warning indicator、要確認 label | 未完了理由と対象を示す |
| locked / unavailable | subdued、lock label | disabled条件を維持 |

- stepperは進捗と現在地を示し、不要な装飾やfake progressを加えない。
- stepの番号、順序、navigation state、CTAを変更しない。
- current stepとPrimary CTAを近接させ、次に何をすべきかを明確にする。
- stepper上のclickabilityは既存条件を維持し、visual redesignで遷移可能範囲を広げない。

## 15. PROGRESS CONTRACT

| Type | 用途 | 禁止 |
|---|---|---|
| determinate | 実際の割合、件数、完了項目が計測可能 | 根拠のない%表示 |
| indeterminate | 完了時点が不明な短い処理 | fakeな進行率 |
| AI processing | AIの対象と処理stageを説明 | AIが賢そうに見えるだけの演出 |
| workflow completion | Proposal step / Quality Gateの完了度 | API処理とworkflow完了の混同 |

Progressは「何が終わったか」と「何が残っているか」を補助し、処理完了・Quality Gate完了・download unlockの条件を変更しない。

## 16. ICON CONTRACT

- icon size: inline 16px、standard 18px、major action 20pxを基準。
- stroke: lucide系の一貫したstrokeを基本とし、weightで状態を過度に表現しない。
- visible labelがあるiconはdecorative (`aria-hidden=true`)にする。
- icon-only buttonは必ずaccessible nameを持つ。
- status iconは意味を補助し、色だけに依存しない。
- decorative iconは情報階層を乱さないサイズ・contrastにする。
- AI sparkleは汎用AIアイコンにしない。AI-assistedはlabel、processingはstage/progressを優先する。
- danger、warning、confirmedには意味が明確なiconを使用するが、icon単独で完結させない。

## 17. COMPONENT STATE MATRIX

`—`はそのPrimitiveに意味のあるstateを作らないことを示す。無理に全stateを実装しない。

| Primitive | default | hover | focus | active | selected | disabled | loading | error | success |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Button | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| IconButton | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| Input | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ | ✓ |
| Textarea | ✓ | — | ✓ | — | — | ✓ | ✓ | ✓ | ✓ |
| Select | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ | ✓ | — |
| Checkbox | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Card | ✓ | ✓ (interactive) | ✓ (interactive) | ✓ (interactive) | ✓ | — | — | — | — |
| Panel | ✓ | — | — | — | — | — | ✓ | ✓ | ✓ |
| Badge | ✓ | — | — | — | — | — | — | — | — |
| Status | ✓ | — | — | — | — | — | ✓ | ✓ | ✓ |
| Alert | ✓ | — | — | — | — | — | — | ✓ | ✓ |
| EmptyState | ✓ | — | — | — | — | — | — | — | — |
| Skeleton | — | — | — | — | — | — | ✓ | — | — |
| Spinner | — | — | — | — | — | — | ✓ | — | — |
| Progress | — | — | — | — | — | — | ✓ | ✓ | ✓ |
| Modal | ✓ | — | ✓ | — | — | — | ✓ | ✓ | — |
| Drawer | ✓ | — | ✓ | — | — | — | ✓ | — | — |
| Table | ✓ | ✓ (row action) | ✓ | ✓ (row action) | ✓ (row) | — | ✓ | ✓ | ✓ |
| Tabs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — | — |
| Stepper | ✓ | — | ✓ (if clickable) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Status-specific meanings such as AI-processing、human-review、confirmedはStatus / Badge / Stepper / Progressのsemantic layerで表し、全Primitiveへ一律追加しない。

## 18. DENSITY MATRIX

| Primitive | Comfortable | Compact |
|---|---|---|
| Button | default 44px、padding 16px | compact 36px visual、hit 44px、padding 12px |
| Field | control 44px、field gap 20px | control 36〜44px、field gap 12px |
| Card | padding 20px、section gap 24〜32px | padding 12〜16px、gap 16〜20px |
| Panel | padding 24px、descriptionを十分表示 | padding 16px、metadataを整理 |
| Table | row 56〜64px、cell 12px 16px | row 40〜48px、cell 8px 12px |
| Tabs | 44px以上、label間隔12px | 40px visual、hit 44px、label間隔8px |
| Stepper | title + descriptionを表示 | title + status中心、detailは近接panelへ |

Comfortableは利用者の認知負荷を下げ、Compactは管理者の比較・監視を助ける。component API、semantics、accessibilityは共通で、densityだけが変わる。

## 19. LEGACY COMPONENT MIGRATION

| Classification | 現行 | 方針 |
|---|---|---|
| KEEP TEMPORARILY | `v80-*`, `v81-*`, `advanced-foldout`, `#*-panel`, `data-testid` | selector・navigation・panel契約のため維持 |
| ALIAS | `.primary-button`, `.secondary-button`, `.danger-button`, `.text-button`, `.icon-button` | Button / IconButtonへCSS alias。accessible nameとstate条件を維持 |
| ALIAS | `.field`, field grids、native form controls | Field / FormLayoutへ段階接続 |
| ALIAS | `.status-note`, `.status-message-*`, `.decision-pill`, `.status-pill`, `.warning-box` | Status / Alert / Badgeへsemantic mapping |
| ALIAS | `.table-scroll`, `.usage-dashboard-table` | Table / TableScrollへ接続 |
| MIGRATE | 各種`*-card`, `*-panel`, `*-grid` | semantic conditionを判定してCard / Panel / Sectionへ移行 |
| MIGRATE | `.skeleton-*`, `.pp-spinner`, `.pp-progress` | Loading primitivesへ統合 |
| DEPRECATE LATER | 同一意味の別名class、cafe系visual alias、局所button variant | 全参照とE2Eを確認後に削除候補 |

### E2E-safe migration strategy

1. 新componentが既存class、test id、role、ARIA、idを受け取れるcompatibility adapterを定義する。
2. 1画面ずつ内部実装を置換し、DOM上の契約とAPI条件を比較する。
3. visual changeとsemantic/functional changeを分離する。
4. existing locatorが対象要素を引き続き特定できることを確認する。
5. legacy classを直ちに削除せず、aliasの利用状況を記録する。
6. 最後に未使用legacy classを別タスクでdeprecateする。

特にbutton accessible name、form label、panel id、`.v80-sidebar`、`.guided-step-card`、`.table-scroll`、modal roleは変更しない。

## 20. COMPONENT GOVERNANCE

### 新variantを追加してよい条件

- semantic purposeが既存variantと異なる。
- state、accessibility、functional behaviorにも意味の差がある。
- 2つ以上の画面で再利用される見込みがある。
- CSSだけの個別調整ではなく、component APIとして明示する価値がある。
- user/adminの両方または明確なdomain boundaryで説明できる。

### 新Primitiveを追加してよい条件

- 既存Primitiveの責務では安全に表現できない独立したsemantic responsibilityがある。
- 少なくとも2つの実利用箇所がある、または重大なaccessibility契約を共通化できる。
- 既存Primitiveのvariant追加では責務が曖昧になる。
- Level 1 contractとmigration planが文書化されている。

### 既存componentを再利用すべき条件

- 同じsemantic role、同じstate、同じ操作優先順位を持つ場合。
- 見た目だけが異なる場合はvariantではなくtoken / densityで解決できる場合。
- page-specific markupが必要でも、Field、Button、Status、Panel等の内部primitiveは再利用する。

### Page-specific CSSを許容する条件

- page固有のlayout構造であり、他画面のsemantic componentへ漏れない。
-既存primitiveのstate・focus・disabled・ARIAを上書きしない。
- design tokenを使用し、hard-coded valueを増やさない。
- 同じ形が2箇所に現れた時点でprimitiveまたはpattern化を検討する。
- E2E selectorをstyling hookにせず、既存classをcompatibilityとして扱う。

### Review gate

新component・variant・page-specific CSSのPRまたは設計変更では、semantic clarity、accessibility、migration safety、user/admin coherence、variant countを確認する。

## 21. QUALITY CHECK

| 評価項目 | Score | 理由 |
|---|---:|---|
| semantic clarity | 95 | Primitive、Panel、Card、Section、Status、Alertの境界を明文化 |
| visual consistency | 93 | variant、density、Foundation tokenへの接続を制限 |
| accessibility | 94 | label、ARIA、focus、touch target、status semanticsを契約化 |
| migration safety | 96 | legacy alias、E2E-safe strategy、Level 1 freezeを明示 |
| user/admin coherence | 95 | 同じPrimitiveをdensityで共有 |
| variant discipline | 94 | semantic差がないvariantを禁止 |
| operational usability | 94 | Primary CTA、state、loading、review、tableを業務順で定義 |
| non-generic AI | 95 | AI-assisted、processing、human-review、confirmedを分離 |

全項目90点以上。実装前に、代表画面のButton、Proposal Flow、Quality Gate、Admin Tableでcontract適合性を確認する。

## 22. IMPLEMENTATION GATE

実装開始前に以下を満たす。

- UI Contract Freezeとの照合が完了している。
- 既存class、test id、role、ARIA、panel idのcompatibility strategyがある。
- componentごとのsemantic purposeと禁止用途が明確である。
- light/dark、comfortable/compact、state matrixが定義されている。
- representative screen designでvisual hierarchyとoperational usabilityを確認する。
- TSX、CSS、testsの変更は別タスクとして切り離す。

