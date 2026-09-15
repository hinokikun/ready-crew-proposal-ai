# Ready Crew Proposal AI — FINAL VISUAL MASTER

Status: `VISUAL_SOURCE_OF_TRUTH: LOCKED`

この文書はReady Crew Proposal AIのDesign Refreshにおける正式なVisual Source of Truthである。Presentation Master、M30、rendererの仕様ではない。旧資料と本Visual Masterが競合する場合は、本Visual Masterを優先する。

## 1. Brand Identity

- 正式ブランド名: 提案クエスト
- English: TEIAN QUEST
- Main message: AIと、いい提案をつくる冒険に出よう！
- Supporting brand message: AIで、はたらくをもっと前へ。
- English supporting message: GOOD IDEAS. GOOD PROPOSALS. A BRIGHTER TOMORROW.
- Visual concept: AI × PROPOSAL × ADVENTURE

ファミコン / 16bitゲームを想起させるPixel Artをブランド世界観とする。ただし「ゲームを作る」のではなく、実用的な提案業務アプリを冒険体験として表現する。

## 2. Core Visual Principle

UIは、Business UI LayerとAdventure / Brand Layerの2層で構成する。

### A. Business UI Layer

- white / pale blue content surface
- readable forms
- tables
- charts
- settings
- admin
- proposal editing
- estimate
- download
- operational information

### B. Adventure / Brand Layer

- pixel-art sky
- clouds
- city
- castle
- forest
- grass
- brick/platform motifs
- robot characters
- speech bubbles
- stage/progress expressions

Business UI Layerの可読性・操作性を最優先する。Pixel Artをフォームや大量の情報の背景に直接敷かず、入力、確認、判断、ダウンロードなどの操作を妨げない。「ゲーム風業務アプリ」であり、「業務情報までゲームUIに変換する」ことは禁止する。

## 3. AI Robot Team

5体のAI Robotをブランドの主要キャラクターとして使用する。

| Robot color | Role concept | Product feedback role |
|---|---|---|
| Green | Analysis | 案件分析、入力受付、情報読み取り |
| Flame / Orange | Strategy | 戦略、勝ち筋、次アクション |
| Pink | Research | 調査、比較、根拠発見 |
| Red | Idea | アイデア、提案構成、内容整理 |
| Brown / Tan | Final Check | 仕上げ、Quality Gate、完成確認 |

キャラクターは装飾だけではなく、AI processing / guidance / review / completion / warningなど現在の状態をユーザーへ伝える補助役として使用する。キャラクターやspeech bubbleがCTA、入力欄、テーブル、重要情報を隠してはならない。画面ごとに全5体を必ず表示する必要はない。

## 4. Desktop Layout

Reference viewport: `1440px`

Authenticated operational pagesの基本構造:

- dark navy left sidebar
- dark navy top/header area
- white / pale blue main workspace
- pixel-art environment around peripheral/background regions
- contextual robot character near lower or secondary visual region

Proposal creation flowではstep/progress indicatorを明示する。Analytics / History / Admin / Settingsなど情報密度が高いページではPixel Art量を減らし、Business UIを優先する。Auth、Loading、Error、404、Completionなどのspecial state pageでは通常ページより強いPixel Art表現を許可する。

## 5. Mobile Layout

Reference viewport: `390px`

Desktopの縮小は禁止する。

- dark navy top header
- single-column content
- bottom navigation for primary destinations
- hamburger / drawer for secondary destinations
- contextual robot near bottom area
- primary CTA reachable without decorative obstruction

入力フォーム、テーブル、カード等は390pxに合わせて再構成する。Desktop sidebarをそのまま狭く表示しない。

## 6. Navigation

Primary authenticated navigationの視覚的な基本候補:

- Home
- Proposal creation
- Review / Output
- History
- Analytics
- Settings

AdminやHelp等は権限・画面構造に応じてsecondary navigationとして扱える。ただし実際のnavigation state、permission、route/view behaviorは既存LEVEL 1 FROZEN CONTRACTを変更しない。

Visual Masterは既存機能を再設計するものではなく、既存機能の視覚体系を統一するものとする。

## 7. Color Semantics

| Semantic color | Usage |
|---|---|
| Dark Navy | application shell / navigation / strong framing |
| Bright Blue | normal primary action / selected state |
| Red | error / destructive / regeneration / exceptionally strong game-style CTA |
| Green | success / completed / positive state |
| Yellow / Orange | tips / caution / stage accent / supporting emphasis |
| White / Pale Blue | business content surface |

状態を色だけで伝えず、text / icon / shape等を併用する。

## 8. Typography

業務本文は高可読な日本語Sans Serifを使用する。Pixel / game-style typographyはlogo、stage title、special completion expression、brand headline等に限定する。フォームラベル、本文、テーブル、設定、管理画面などをPixel Fontにしない。可読性をブランド表現より優先する。

## 9. Component Direction

以下はBusiness UIとして統一する。

- Button
- FormField
- Input
- Select
- Textarea
- Card
- Panel
- Badge
- Status
- Alert
- Table
- Tabs
- Stepper
- Modal
- Drawer
- Progress
- Skeleton
- Spinner

これらにはPixel Artを直接描き込みすぎない。Pixel Artは主にshell / scenery / mascot / stage indicator / brand accentとして利用する。

## 10. Screen Families

同一IDに複数のVisual案が存在する場合、それらを別画面として数えない。variant / revision / desktop-mobile representationとして扱う。

### Authentication

`AUTH-01`, `AUTH-02`, `AUTH-03`, `AUTH-04`, `LOGIN`, `SIGNUP`

### Onboarding

`ONBOARD`

### Core

`HOME`, `USER-01`, `USER-02`, `CREATE`

### AI Proposal Flow

`AI-01`, `AI-02`, `AI-03`, `AI-04`, `USER-03`, `USER-04`, `AI-05`, `USER-05`, `COMPLETE`

### Proposal Domain

`CASE`, `CLIENT`, `COMPETITION`, `STRATEGY`, `GENERATE`, `EDIT`, `PREVIEW`, `DOWNLOAD`, `DETAIL`, `ESTIMATE`

### Business Management

`HISTORY`, `ANALYTICS`

### Account

`SETTINGS`, `PROFILE`, `NOTIFICATION`, `PASSWORD`

### Administration

`ADMIN`

### Support

`HELP`, `GUIDE`, `FAQ`, `CONTACT`, `System Information`

### System States

`LOADING`, `ERROR`, `NOTFOUND / 404`

## 11. State Design

正式なVisual Design対象とする状態:

- initial
- loading
- AI processing
- insufficient information
- success
- warning
- error
- permission denied
- authentication checking
- empty
- retry
- completion

AI processingではAI Robot Teamを積極的に利用できる。Completionでは`STAGE CLEAR`などのゲーム的演出を許可する。ただし通常業務画面では演出を抑制する。

## 12. Responsive Principle

- Desktop reference: `1440px`
- Mobile reference: `390px`

既存Design System Foundationのresponsive rulesを尊重しながら、この2つをHuman Visual Review基準viewportとする。中間viewportでも破綻しないこと。DesktopからMobileへの単純scaleは禁止する。

## 13. Accessibility / Usability

- sufficient text contrast
- visible focus
- keyboard usability
- minimum practical touch target
- status not represented by color alone
- decorative Pixel Art should not become semantic noise
- motion should respect reduced-motion preference
- content remains usable if decorative assets fail

## 14. LEVEL 1 FROZEN CONTRACT

`DESIGN_SYSTEM_MIGRATION_INVENTORY.md`で定義したLEVEL 1を絶対維持する。Visual redesignの都合で以下を変更しない。

- data-testid
- role
- aria attributes
- accessible names
- panel IDs
- navigation state
- API call conditions
- permission gating
- Proposal step order
- loading behavior
- disabled behavior
- output/download semantics
- modal semantics
- Quality Gate behavior
- retry behavior

必要な場合は既存DOM contractの上にvisual stylingを適用する。

## 15. Compatibility

Legacy CSS/class namesは移行途中ではCompatibility Layerとして残す。visual migrationのために一度に既存classを大量削除せず、新旧component/styleを段階移行する。

## 16. Explicit Non-Goals

このVisual Master作成時点では以下を行わない。

- Frontend implementation
- Backend changes
- API changes
- DB changes
- OpenAI API changes
- Feature Flag changes
- Production changes
- Render changes
- Vercel changes
- Presentation Master changes
- M30 changes
- renderer changes
- deployment
- commit/push unless separately instructed

## 17. Implementation Philosophy

Codexは新しいデザインを独自に考えない。ChatGPT/Humanで承認されたVisual Masterを忠実に実装する役割とする。

実装フェーズは小さく分割する。

1. tokens / global foundation
2. application shell
3. navigation
4. representative Home
5. Proposal input
6. AI processing
7. Review / Output
8. secondary operational pages
9. Admin / Settings / Help
10. system states
11. responsive corrections
12. Human Visual Review corrections

各主要フェーズでDesktop 1440px / Mobile 390pxをHuman Visual Reviewしてから次へ進む。

## 18. Visual Quality Guardrails

禁止事項:

- generic SaaS dashboardへの回帰
- excessive gradients
- excessive glassmorphism
- random rounded cards everywhere
- emojiによるPixel Art代替
- unrelated stock illustration
- every area becoming game UI
- decorative characters covering controls
- unreadable pixel fonts in business content
- excessive animation
- arbitrary redesign by Codex
- changing functionality for visual convenience

目標は、「一目で提案クエストと分かる」ことと「実際の提案業務で毎日使える」ことの両立である。

