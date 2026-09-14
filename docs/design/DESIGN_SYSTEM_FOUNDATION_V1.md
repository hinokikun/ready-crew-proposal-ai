# Ready Crew Proposal AI Design System Foundation v1

基準: UI Contract Freeze / `DESIGN_CONCEPT_V1.md` / `quietly capableなProposal Business Workbench`  
対象: Foundation仕様のみ  
対象外: 既存TSX/CSS/testsの変更、Production、Render/Vercel、Feature Flag、OpenAI API、Presentation Master、M30、renderer関連

この文書は実装値の採用を承認するためのFoundation仕様である。実装時もLEVEL 1 Functional Contractを変更しない。既存classは移行期間中aliasとして残し、semantic tokenとcomponent tokenを追加して段階移行する。

## 1. COLOR FOUNDATION

Primitive paletteとsemantic tokenを分離する。primitiveは値の保管、semanticは意味の表現、component tokenはUI部品への適用を担当する。画面ではsemantic tokenを直接使い、primitiveを直接参照しない。

### Primitive palette

| Family | Light primitive | Dark primitive | 用途 |
|---|---|---|---|
| Neutral | N0 `#FFFFFF`, N25 `#FCFDFE`, N50 `#F7F9FC`, N100 `#EEF2F6`, N200 `#D9E0E8`, N400 `#98A5B5`, N600 `#526173`, N800 `#263444`, N950 `#111A24` | D0 `#111820`, D25 `#151E28`, D50 `#1B2632`, D100 `#253341`, D200 `#344454`, D400 `#718398`, D600 `#AAB7C5`, D800 `#E1E8EF`, D950 `#F5F8FB` | background、surface、text、border |
| Blue | B50 `#EAF2FF`, B100 `#D8E7FF`, B300 `#8DB6FF`, B600 `#155EEF`, B700 `#0F49C8`, B900 `#123A78` | DB50 `#162A45`, DB100 `#1B3A63`, DB300 `#5F98F2`, DB500 `#78AFFF`, DB600 `#9CC6FF`, DB900 `#E2EEFF` | brand、action、focus |
| Teal | T50 `#E8F7F5`, T100 `#CDEDE8`, T500 `#168A7A`, T700 `#0E6258`, T900 `#0B3E3A` | DT50 `#153A38`, DT100 `#1D504B`, DT400 `#62C5B7`, DT500 `#76D6C7`, DT800 `#D1F3EE` | AI-assisted、information |
| Green | G50 `#EAF8F0`, G100 `#D2F1DF`, G600 `#168A4A`, G700 `#0E6B39` | DG50 `#163A29`, DG100 `#1D5537`, DG400 `#67C78E`, DG500 `#82D9A3`, DG800 `#D7F6E3` | success、confirmed |
| Amber | A50 `#FFF8E7`, A100 `#FDECC2`, A600 `#B54708`, A700 `#8A3506` | DA50 `#453218`, DA100 `#60451E`, DA400 `#E6B85E`, DA500 `#F2C978`, DA800 `#FFF0C7` | warning、human review |
| Red | R50 `#FFF1F0`, R100 `#FFD9D5`, R600 `#C43227`, R700 `#A32620` | DR50 `#442322`, DR100 `#61302C`, DR400 `#F18B82`, DR500 `#FFAAA0`, DR800 `#FFE0DC` | danger、error |

### Semantic tokens: Light / Dark

| Semantic token | Light HEX | Dark HEX | 役割 |
|---|---:|---:|---|
| `background` | `#F7F9FC` | `#111820` | アプリ全体の長時間利用向け背景 |
| `surface` | `#FFFFFF` | `#1B2632` | workspace、通常panelの基盤 |
| `surface-subtle` | `#F2F5F8` | `#253341` | 補助領域、sectionの弱い区切り |
| `surface-raised` | `#FFFFFF` | `#253341` | 独立した判断単位、popover、raised panel |
| `surface-selected` | `#EAF2FF` | `#1B3A63` | 選択中、active navigation、selected row |
| `text-primary` | `#1D2939` | `#F5F8FB` | 本文、見出し、主要値 |
| `text-secondary` | `#526173` | `#D4DEE8` | 説明、補助本文 |
| `text-muted` | `#667085` | `#AAB7C5` | metadata、caption、補助情報 |
| `text-inverse` | `#FFFFFF` | `#111820` | 濃色action上の文字 |
| `border-default` | `#D9E0E8` | `#344454` | 通常の境界 |
| `border-strong` | `#98A5B5` | `#718398` | table、panel、重要な区切り |
| `border-focus` | `#155EEF` | `#9CC6FF` | keyboard focus、入力focus |
| `brand-primary` | `#155EEF` | `#78AFFF` | product identity、active navigation。AI状態そのものではない |
| `brand-hover` | `#0F49C8` | `#9CC6FF` | brand要素のhover |
| `brand-subtle` | `#EAF2FF` | `#162A45` | brandの淡い背景 |
| `action-primary` | `#155EEF` | `#78AFFF` | 画面の主要操作 |
| `action-primary-hover` | `#0F49C8` | `#9CC6FF` | primary action hover |
| `action-secondary` | `#FFFFFF` | `#1B2632` | secondary actionのsurface。borderとtextで識別 |
| `success` | `#168A4A` | `#82D9A3` | 完了、利用可能、確定済み |
| `success-subtle` | `#EAF8F0` | `#163A29` | successの背景 |
| `warning` | `#B54708` | `#F2C978` | 要確認、期限、部分的な不足 |
| `warning-subtle` | `#FFF8E7` | `#453218` | warningの背景 |
| `danger` | `#C43227` | `#FFAAA0` | 失敗、停止、破壊的操作 |
| `danger-subtle` | `#FFF1F0` | `#442322` | dangerの背景 |
| `info` | `#155EEF` | `#9CC6FF` | 補足、non-blocking情報 |
| `info-subtle` | `#EAF2FF` | `#162A45` | infoの背景 |
| `AI-assisted` | `#168A7A` | `#76D6C7` | AIが整理・提案に関与した状態。brandとは別の意味 |
| `AI-processing` | `#0E6258` | `#62C5B7` | AI処理中、progress、processing indicator |
| `human-review` | `#B54708` | `#F2C978` | 人の確認・判断が必要な状態 |
| `confirmed` | `#168A4A` | `#82D9A3` | 人が確認・確定した状態 |
| `disabled-background` | `#EEF2F6` | `#253341` | 操作不可controlの背景 |
| `disabled-text` | `#98A5B5` | `#718398` | 操作不可controlの文字 |

### Color rules

- statusは色だけで識別しない。必ずラベル、アイコン、位置、または説明文を併用する。
- `brand-primary`はブランド・navigation・主要操作を示し、AIの存在を示さない。
- `AI-assisted`はAIが関与したこと、`human-review`は人の確認が必要なこと、`confirmed`は確定済みであることを示す。
- neutral surfaceとborderで階層を作り、色面積を増やして目立たせない。
- primary actionは1画面1主目的を基本とする。
- dark modeは色反転ではなく、semantic roleごとにコントラストと意味を維持する。

## 2. TYPOGRAPHY FOUNDATION

### Font family strategy

- 第一候補: `Inter`, `Noto Sans JP`
- 日本語fallback: `Hiragino Sans`, `Yu Gothic`, `Meiryo`, `system-ui`, `sans-serif`
- 業務UI全体はsans-serif。display用の装飾書体は使用しない。
- 数字・KPIはtabular figuresを優先し、桁比較を容易にする。
- technical identifier、version、JSON、status codeのみmonospaceを許可する。

### Type scale

| Style | Size | Weight | Line-height | Letter-spacing | 用途 |
|---|---:|---:|---:|---:|---|
| `display` | 32px / 2rem | 700 | 1.25 / 40px | -0.01em | ホーム等の限られた主見出し |
| `page-title` | 28px / 1.75rem | 700 | 1.35 / 38px | -0.01em | ページタイトル |
| `section-title` | 20px / 1.25rem | 700 | 1.4 / 28px | 0 | section見出し |
| `subsection-title` | 16px / 1rem | 700 | 1.5 / 24px | 0 | card・panel内見出し |
| `body` | 15px / 0.9375rem | 400 | 1.7 / 25.5px | 0 | 日本語本文・説明 |
| `body-compact` | 14px / 0.875rem | 400 | 1.55 / 21.7px | 0 | 管理・table補助本文 |
| `label` | 14px / 0.875rem | 600 | 1.45 / 20.3px | 0 | form label、row label |
| `helper` | 13px / 0.8125rem | 400 | 1.5 / 19.5px | 0 | 入力補助、validation説明 |
| `caption` | 12px / 0.75rem | 500 | 1.45 / 17.4px | 0.01em | metadata、日時、eyebrow |
| `button` | 14px / 0.875rem | 600 | 1 / 20px | 0 | button accessible name |
| `table-header` | 12px / 0.75rem | 700 | 1.35 / 16.2px | 0.01em | table column header |
| `table-cell` | 13px / 0.8125rem | 400 | 1.45 / 18.9px | 0 | 管理table cell |
| `numeric / metric` | 24px / 1.5rem | 700 | 1.2 / 28.8px | -0.01em | KPI、件数、確率 |

### Typography rules

- 日本語長文はbody 15px以上と1.7前後のline-heightを基本とする。
- 1行の長さは本文でおおむね45〜70文字相当を目安にし、横幅いっぱいに伸ばさない。
- 数字と単位を分離し、KPIは桁、単位、補足を一貫して配置する。
- 英数字混在の案件名・企業名・URLはwrapとoverflowを個別に定義する。
- font weightは400 / 500 / 600 / 700に限定し、太字で階層不足を補わない。
- mobileではpage-titleを24px、displayを28pxまで下げるが、bodyとlabelの可読性は下げない。

## 3. SPACING FOUNDATION

Base unitは4px。主なレイアウト間隔は8px単位を優先する。

| Token | Value | 用途 |
|---|---:|---|
| `space-0` | 0px | reset |
| `space-1` | 4px | iconとlabelの微小間隔 |
| `space-2` | 8px | inline gap、caption間隔 |
| `space-3` | 12px | control内、compact gap |
| `space-4` | 16px | field gap、card内標準間隔 |
| `space-5` | 20px | subsection間隔 |
| `space-6` | 24px | panel padding、section間隔 |
| `space-7` | 28px | page内主要区切り |
| `space-8` | 32px | page padding、large section |
| `space-10` | 40px | 大きな導入領域 |
| `space-12` | 48px | desktop page上下余白 |
| `space-16` | 64px | hero相当の限定用途 |

### Recommended application

| 用途 | Comfortable | Compact / Admin |
|---|---:|---:|
| desktop page padding | 32px | 24px |
| mobile page padding | 16px | 16px |
| section gap | 32px | 24px |
| panel padding | 24px | 16px |
| card padding | 20px | 12px〜16px |
| form field gap | 20px | 12px |
| button gap | 12px | 8px |
| table cell padding | 12px 16px | 8px 12px |
| admin compact spacing | — | section 20px、row 8px |

ページpaddingとpanel paddingを混同しない。magic numberが必要な場合は、既存UIとの互換理由をmigration noteに記録する。

## 4. RADIUS FOUNDATION

すべてをpillや丸いcardにしない。操作対象と情報容器でradiusを使い分ける。

| Token | Value | 主な用途 |
|---|---:|---|
| `radius-none` | 0px | table、flush section、精密な境界 |
| `radius-xs` | 4px | compact control、table内badge |
| `radius-sm` | 6px | button、input、select、small card |
| `radius-md` | 8px | standard card、panel、dropdown |
| `radius-lg` | 12px | modal、major workspace panel |
| `radius-xl` | 16px | auth card、限定的なhero surface |
| `radius-pill` | 999px | status badge、tag、compact status indicatorのみ |

Rules:

- button / input / select: `radius-sm`
- card: `radius-md`
- panel: `radius-md`、主要workspaceのみ`radius-lg`
- modal / drawer: `radius-lg`
- badge: `radius-pill`。情報容器には使用しない
- radius変更でbuttonのtouch targetやtext wrappingを壊さない

## 5. SHADOW / ELEVATION FOUNDATION

borderとsurface hierarchyを第一にし、shadowはlayerが前面に出る必要がある場合だけ使う。

| Token | 値の方針 | 使用場面 |
|---|---|---|
| `elevation-none` | none | page、通常section、table |
| `elevation-xs` | 0 1px 2px / low alpha | selected card、controlの微細な分離 |
| `elevation-sm` | 0 4px 12px / low alpha | dropdown、浮かぶaction group |
| `elevation-md` | 0 12px 28px / medium alpha | modal内panel、重要なfloating workspace |
| `elevation-overlay` | 0 20px 48px / overlay alpha | modal、drawer、blocking dialog |

使ってよい場面:

- 通常surfaceから前面に出るdropdown、drawer、modal
- 背景との境界だけでは誤操作しやすいfloating control
- selected stateをborderだけで識別しにくい場合の補助

使ってはいけない場面:

- 全cardへの一律shadow
- dashboardの情報量を隠すための浮遊表現
- 同じ階層のpanel同士をshadowで競わせること
- glassmorphism、透明blur、neon glow

## 6. CONTROL SIZE FOUNDATION

Defaultはdesktopとmobileで同一の操作理解を保ち、touch targetは最低44pxを確保する。

| Size | Button height | Input/select height | Horizontal padding | Icon |
|---|---:|---:|---:|---:|
| `compact` | 36px | 36px | 12px | 16px |
| `default` | 44px | 44px | 16px | 18px |
| `large` | 52px | 52px | 20px | 20px |

- compactでも実際のクリック領域は44px未満にしない。visual heightとtouch targetを分離してよい。
- Primary CTAはdefault、重要な生成・完了操作はlargeを候補とする。
- table row action、admin toolbarはcompactを候補とする。
- IconButtonはvisual 36pxまたは40pxでも、interactive hit areaは44px以上。
- disabled、loading、focusでcontrol heightが変わらない。

## 7. MOTION FOUNDATION

業務状態の理解を助けるための短いmotionだけを採用する。

| Token / interaction | Value |
|---|---:|
| `motion-duration-instant` | 0ms |
| `motion-duration-fast` | 120ms |
| `motion-duration-base` | 180ms |
| `motion-duration-slow` | 240ms |
| `motion-easing-standard` | cubic-bezier(0.2, 0, 0, 1) |
| `motion-easing-emphasis` | cubic-bezier(0.2, 0.8, 0.2, 1) |
| hover / focus | 120ms |
| drawer | 180〜240ms |
| modal | 180ms |
| loading indicator | 1000〜1400ms loop |

- hover、focus、selected、button feedbackはfast。
- drawer・modalはbase〜slow。内容の到着を遅らせない。
- loadingは処理中を伝える場合のみ使用。常時pulse、sparkle、floatingは使用しない。
- success/errorは短いtransitionで出現させるが、messageの存在条件は変更しない。
- `prefers-reduced-motion: reduce`ではanimationを停止またはほぼ即時化し、scroll behaviorも抑制する。

## 8. BREAKPOINT FOUNDATION

既存の複数breakpointをいきなり削除せず、意味のある4段階へ整理する。

| Token | Range | 主目的 |
|---|---|---|
| `mobile` | 0〜639px | 1列、drawer、Primary Action優先 |
| `tablet` | 640〜899px | 1〜2列、compact navigation、段階的stack |
| `desktop` | 900〜1199px | sidebar + main、標準workspace |
| `wide` | 1200px以上 | 広いworkspace、複数column、table余白 |

### Existing breakpoint migration

| Existing | Migration interpretation |
|---:|---|
| 560 | mobile内のauth / narrow form edge caseとして一時保持 |
| 640 | `mobile`→`tablet`境界へalias |
| 720 | tablet内のform・guided flow補助条件として一時保持 |
| 760 | tablet内のguided / studio補助条件として一時保持 |
| 900 | `tablet`→`desktop`境界へalias |
| 1024 | desktop内のgrid density補助条件として一時保持 |
| 1080 | desktop内のsidebar / layout補助条件として一時保持 |

移行時はCSSの既存順序と動作を壊さず、semantic breakpoint aliasを追加してから段階的に統合する。E2Eのmobile menu、sidebar、table overflowの挙動を先に固定する。

## 9. DENSITY SYSTEM

UserとAdminで別Systemを作らず、同じcomponent tokenにcomfortable / compactのdensity presetを与える。

| 属性 | Comfortable | Compact |
|---|---:|---:|
| 主用途 | user home、proposal flow、review | admin、analytics、logs、data-heavy manager view |
| panel padding | 24px | 16px |
| card padding | 20px | 12〜16px |
| row height | 56〜64px | 40〜48px |
| control height | 44px | 36〜44px（hit areaは44px） |
| body | 15px / 1.7 | 14px / 1.55 |
| section gap | 32px | 20〜24px |
| metadata | 控えめに表示 | 比較可能な位置に表示 |

Comfortableは迷いを減らす余白、Compactは比較・監視の効率を目的にする。Compactでもstatus、focus、label、danger actionを小さくしすぎない。

## 10. SURFACE HIERARCHY

| Layer | 意味 | border | background | shadow |
|---|---|---|---|---|
| Page | アプリ全体の背景 | 原則なし | `background` | none |
| Workspace | 現在の案件・作業の主領域 | 必要時default | `surface` | none / xs |
| Section | 関連情報のまとまり | defaultまたは余白のみ | `surface-subtle`またはtransparent | none |
| Panel | 判断・操作のまとまり | default / strong | `surface` | none / xs |
| Card | 独立した判断単位 | default | `surface-raised` | xs / none |
| Raised / Overlay | 前面に出る一時領域 | strong | `surface-raised` | sm〜overlay |

- PageやWorkspaceをcard化しない。
- Sectionは情報構造のために使い、装飾目的で入れ子にしない。
- CardはKPI、要約、独立したReview itemなどに限定する。
- panelは操作や判断のまとまり。cardとはsemantic roleを分ける。
- modal / drawer以外でoverlay elevationを使わない。

## 11. STATE VISUAL SYSTEM

| State | 色 | 非色のルール |
|---|---|---|
| default | neutral | 通常border、標準surface、通常label |
| hover | action/brand hover | cursor、borderまたはelevationの微変化 |
| focus | border-focus | 2px以上のfocus indicator、outlineを消さない |
| active | brand/action | navigation indicator、pressed/selected semantics |
| selected | surface-selected | check、indicator、`aria-current`またはselected semantics |
| disabled | disabled tokens | native disabled、操作不可理由を必要時に併記 |
| loading | AI-processing / info | spinner、progress、loading label、操作lock |
| success | success | label、check icon、完了文言 |
| warning | warning | warning icon、要確認文言、次の行動 |
| danger | danger | alert、破壊操作文言、確認・隔離 |
| AI processing | AI-processing | stage、対象、進捗、processing label |
| human review | human-review | 確認CTA、未確定ラベル、必要な判断 |
| confirmed | confirmed | 確定ラベル、check、確定後の操作制限 |

Status semanticsは`role=status`または`role=alert`の既存契約を維持する。色覚差を前提に、色、形、文言、位置のうち最低2つで状態を表す。

## 12. ACCESSIBILITY BASELINE

- 通常本文と背景のcontrastはWCAG AA相当を目標とし、本文4.5:1以上、大きい文字3:1以上を基準にする。
- UI componentの境界・focus indicatorは、背景に対して十分な視認性を確保する。
- focus-visibleは2px以上のoutlineまたは同等の明確なindicatorを持つ。focusを装飾だけで消さない。
- interactive targetは44×44px以上。compact visualでもhit areaは維持する。
- keyboardだけでsidebar、form、tabs、stepper、modal、table actionを操作できる。
- modal open時はfocus管理、close、`role=dialog`、`aria-modal`を維持する。
- loadingは`role=status`またはprogress semantics、errorは`role=alert`を維持する。
- errorは色だけでなく、対象field、原因、修正方法を近接表示する。
- disabledは低contrastにしすぎず、なぜ操作できないかを必要時に説明する。
- reduced motionではanimation・transition・scrollを抑制する。
- heading順、label association、button accessible name、table header semanticsを維持する。

## 13. LEGACY TOKEN MIGRATION

現行`frontend/app/styles/variables.css`を以下の4分類で扱う。

| Classification | 現行token | 方針 |
|---|---|---|
| KEEP | `--background`, `--surface`, `--text`, `--muted`, `--border`, `--primary`, `--primary-hover`, `--success`, `--danger`, `--warning`, `--focus-ring`, `--control-height`, `--transition-fast`, `--transition-base`, z-index tokens | 既存classを壊さないcompatibility aliasとして当面維持 |
| ALIAS | `--pp-color-*`, `--pp-product-name`, `--font-sans`, `--radius-*`, `--shadow-*` | 新semantic / foundation tokenへの参照元として整理。直接利用は段階削減 |
| DEPRECATE | `--surface-muted`, `--surface-subtle`の意味重複、`--cafe-cream`, `--cafe-paper`, `--cafe-sage`, `--cafe-terracotta` | 新規利用禁止。既存CSS向けaliasとして残し、migration完了後に削除候補 |
| NEW | semantic color全般、type scale、spacing scale、density、elevation、control size、breakpoint、state token | Foundation v1の正規token。実装は別タスク |

### Mapping examples

| Existing | Foundation target | 注意 |
|---|---|---|
| `--primary` | `action-primary`または`brand-primary` | 用途を分離。全置換せずselectorの意味を確認 |
| `--primary-hover` | `action-primary-hover`または`brand-hover` | buttonとbrand navigationを分離 |
| `--text` | `text-primary` | dark modeもsemantic roleで切替 |
| `--muted` | `text-secondary`または`text-muted` | metadataと説明本文を分離 |
| `--border` | `border-default` | table・強調境界は`border-strong` |
| `--danger-bg` | `danger-subtle` | status semanticsと併用 |
| `--warning-bg` | `warning-subtle` | human-reviewは別semantic |
| `--cafe-sage` | `surface-subtle`または`info-subtle` | 新規利用禁止。意味ごとに移行 |
| `--control-height` | `control-default-height` | compact/default/largeへ拡張 |
| `--radius-sm` | `radius-sm` | button/inputの基準 |
| `--shadow` | `elevation-sm`またはnone | 一律置換せずsurface階層を確認 |

既存class、`v80-*`、`v81-*`、`advanced-foldout`、button/card/field/status classは、token移行だけでは削除しない。E2E selectorとfunctional contractが安定してからcompatibility layerを整理する。

## 14. TOKEN NAMING CONTRACT

### Primitive

値そのものを表す。画面やcomponentの意味を含めない。

- `primitive-color-blue-600`
- `primitive-space-4`
- `primitive-radius-2`
- `primitive-shadow-1`
- `primitive-duration- fast`

### Semantic

プロダクトの意味を表す。componentをまたいで再利用する。

- `color-background`
- `color-surface-raised`
- `color-text-primary`
- `color-action-primary`
- `color-status-human-review`
- `space-4`
- `radius-md`
- `elevation-sm`
- `motion-duration-fast`

### Component

componentの役割とvariantを表す。semantic tokenを参照し、primitiveを直接参照しない。

- `button-primary-background`
- `button-default-height`
- `field-border-focus`
- `panel-padding-comfortable`
- `table-cell-padding-compact`
- `sidebar-active-indicator`

### Naming rules

- 命名は`category-role-state-variant`の順を基本とする。
- `blue`, `warm`, `cafe`, `ai-purple`等の見た目依存名をsemantic tokenに使わない。
- `ai`はAI関与の意味に限定し、brandの別名にしない。
- `primary`はactionとbrandを文脈上分ける。曖昧なtokenを増やさない。
- 同じtokenに複数の意味を持たせない。
- deprecated tokenは新規コードで使用せず、aliasとして移行期限を記録する。
- token追加時は使用component、state、light/dark、contrast確認を必須とする。

## 15. FOUNDATION QUALITY CHECK

| 評価項目 | Score | 判定理由 |
|---|---:|---|
| quietly capable | 94 | AIを装飾ではなく処理・確認・確定状態として表現している |
| professional | 94 | neutral中心、過剰なshadow・gradientを避け、業務用途の精度を優先 |
| operational | 95 | action、state、attention、density、admin priorityをFoundationに反映 |
| readable | 93 | 日本語長文、数字、英数字、tableを分けたtype scaleを定義 |
| consistent | 92 | user/admin共通system、semantic token、density presetを定義 |
| accessible | 91 | contrast、focus、touch target、keyboard、status semanticsを明文化 |
| non-generic AI | 94 | brand、AI-assisted、human-review、confirmedを意味分離 |
| user/admin coherence | 95 | 同一component systemにcomfortable / compactを提供 |

### 90未満の項目

なし。全項目90以上。実装時には実画面とスクリーンショットでcontrast、long text、table overflow、mobile focusを再確認し、数値上の合格だけで完了としない。

## 16. FOUNDATION IMPLEMENTATION GATE

このFoundation v1を実装へ進める条件:

- Level 1 contract registerと照合済み
- existing tokenを直接置換せずalias strategyが用意されている
- light/darkの全semantic tokenに用途とcontrast確認がある
- comfortable / compactのcomponent behaviorが定義されている
- representative screensでvisual review criteriaを満たす
- TSX、CSS、testsの変更は別タスクとして分離されている

この文書自体は仕様策定であり、既存UIの見た目や機能を変更しない。

