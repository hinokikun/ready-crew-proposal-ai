# ProposalPilot Premium Design Guideline v1

Version: 38.0 Presentation Design Research  
Status: Design specification only. No production implementation.  
Created: 2026-07-17  
Product: ProposalPilot / AI営業秘書  
Purpose: Upgrade the PPTX output standard from "PowerPoint generation" to "executive sales proposal generation."

---

## Page 1. Executive Summary

ProposalPilotのPPTX生成エンジンは、単に文章をスライドへ配置する仕組みではなく、営業担当がそのまま顧客商談で使える「営業提案資料」を生成するデザインエンジンへ進化する必要がある。

このガイドラインは、Microsoft Copilot、Gamma、Beautiful.ai、Canva、McKinsey、BCG、Deloitte、Accenture、IBM Consulting、Amazon PRFAQの公開情報から、営業資料・役員提案資料・コンサル提案資料に共通する設計原則を抽出し、ProposalPilot専用の生成仕様へ落とし込むものである。

結論:

- 1ページ1メッセージを厳守する。
- スライドは文章の置き場ではなく、意思決定を進める画面として設計する。
- すべてのページに異なる情報デザインを持たせる。
- KPI、プロセス、Before/After、比較、ロードマップ、見積、次アクションを視覚的に表現する。
- PowerPoint編集可能な図形・テキスト・アイコンを基本とする。
- 顧客に「この会社なら任せたい」と思わせる品質を最低基準にする。

この文書はVersion39以降の本番PPT生成エンジンの唯一のデザイン仕様書として扱う。

---

## Page 2. Research Sources and Interpretation

### Primary public sources reviewed

- Microsoft Copilot in PowerPoint: Copilot can add slides from a prompt or file, and Microsoft recommends starting from an organization template to preserve theme and design.  
  Source: [Microsoft Support - Create a new presentation with Copilot in PowerPoint](https://support.microsoft.com/en-gb/copilot-powerpoint)

- Microsoft Learn: Copilot is positioned as a way to create professional, engaging, cohesive presentations quickly.  
  Source: [Microsoft Learn - Build effective presentations with AI](https://learn.microsoft.com/en-us/training/modules/present-copilot-microsoft-powerpoint/)

- Gamma: Gamma emphasizes turning prompts, notes, docs, PDFs, and URLs into polished, structured presentations, with adaptive layouts, themes, media, web sharing, and analytics.  
  Source: [Gamma - AI PowerPoint Generator](https://gamma.app/ai-powerpoint)

- Beautiful.ai: Beautiful.ai separates prompt, outline, visual preferences, and generation. It emphasizes shaping the story before slide design, then applying polished design.  
  Source: [Beautiful.ai - Creating a presentation with AI](https://support.beautiful.ai/hc/en-us/articles/12885226948109-Creating-a-presentation-with-AI)

- Beautiful.ai Smart Slides: Smart Slides include title, image, icon-with-text, text boxes, tables, charts, and structural layouts.  
  Source: [Beautiful.ai - Smart Slide Layouts](https://support.beautiful.ai/hc/en-us/categories/40157039009933-Smart-Slide-Layouts)

- Canva: Canva Magic Design creates on-brand presentations from a prompt, then supports editing, brand application, photos, graphics, collaboration, and offline presentation.  
  Source: [Canva - AI Presentation Maker](https://www.canva.com/create/ai-presentations/)

- McKinsey / Minto Pyramid Principle: McKinsey alumni material and Barbara Minto's own site emphasize structure, clarity, MECE grouping, and ideas organized under a single point.  
  Sources: [McKinsey Alumni - Barbara Minto](https://www.mckinsey.com/alumni/news-and-events/global-news/alumni-news/barbara-minto-mece-i-invented-it-so-i-get-to-say-how-to-pronounce-it), [Barbara Minto](https://www.barbaraminto.com/)

- McKinsey Insights: McKinsey publishes articles, reports, white papers, videos, podcasts, and exhibits for executive audiences.  
  Source: [McKinsey - Our Insights FAQ](https://www.mckinsey.com/frequently-asked-questions/our-insights/en)

- BCG: BCG's public materials show structured methods built around purpose, target behaviors, design levers, and implementation.  
  Source: [BCG - Organization Design](https://www.bcg.com/capabilities/organization-strategy/organization-design)

- Deloitte Insights: Deloitte frames research as proprietary analysis that helps leaders navigate what is next and turn aspiration into action.  
  Source: [Deloitte Insights - About](https://www.deloitte.com/us/en/insights/about/about-deloitte-insights.html)

- Accenture Research: Accenture positions research as data-driven thought leadership for leaders anticipating trends and transformation.  
  Source: [Accenture Research](https://www.accenture.com/us-en/about/accenture-research-index)

- IBM Institute for Business Value: IBM emphasizes trusted, technology-based insights to help leaders make better decisions and investments.  
  Source: [IBM Institute for Business Value](https://www.ibm.com/thought-leadership/institute-business-value)

- Amazon Working Backwards / PRFAQ: Amazon starts from the customer experience and works backward to the solution; PRFAQ captures value, assumptions, economics, and hard questions before execution.  
  Sources: [AWS - Prioritize customer needs](https://docs.aws.amazon.com/wellarchitected/latest/devops-guidance/oa.ti.6-prioritize-customer-needs-to-deliver-optimal-business-outcomes.html), [About Amazon - Working Backwards](https://www.aboutamazon.com/news/workplace/an-insider-look-at-amazons-culture-and-processes)

### Interpretation policy

This guideline does not copy visual assets, layouts, copyrighted slides, or proprietary documents from these companies. It extracts reusable design principles:

- Executive clarity
- Structured reasoning
- Visual hierarchy
- Evidence-led messaging
- Customer-outcome orientation
- On-brand consistency
- Actionable next steps

---

## Page 3. What "One Message Per Page" Means

1ページ1メッセージとは、各スライドが「1つの判断」「1つの理解」「1つの行動」を前進させる状態を指す。

悪い例:

- タイトルが「現状課題」
- 本文が複数の論点を箇条書きで羅列
- 図表、KPI、見積、リスクが同居
- 何を理解すればよいのか不明

良い例:

- タイトルが「確認作業の属人性が、登録品質と処理速度のボトルネックになっている」
- 画面中央に課題構造を図解
- 下部に1つだけ示唆を置く
- 次ページでBefore/Afterへ自然につながる

ProposalPilot適用ルール:

- スライドタイトルは原則として結論文にする。
- タイトルは単語ではなく、主張・判断・示唆を書く。
- 1ページに主要メッセージは1つだけ。
- 補足情報は最大3ブロックまで。
- 1ページ内に「課題」「解決策」「見積」「次アクション」を混在させない。
- すべてのページに「このページで相手に何を理解してほしいか」を内部的に持たせる。

---

## Page 4. Information Density Rules

営業提案資料では、情報量は少なすぎても不安を生み、多すぎても読まれない。ProposalPilotは、読み上げ資料ではなく、商談中に説明しやすい資料を生成する。

### Density targets

| Item | Standard | Hard limit |
|---|---:|---:|
| Main message | 1 | 1 |
| Supporting blocks | 2-4 | 5 |
| Body text per slide | 80-180 Japanese characters | 260 |
| Bullet count | 3-5 | 6 |
| KPI cards | 3-4 | 5 |
| Process steps | 3-6 | 7 |
| Table columns | 3-4 | 5 |
| Icons per page | 3-8 | 10 |

### White space

- Minimum outer margin: 56 px on 1280x720 canvas.
- Recommended outer margin: 64-80 px.
- Between major blocks: 28-48 px.
- Between cards: 16-28 px.
- No text box should visually touch card borders.

### Typography

| Text role | Recommended size | Minimum |
|---|---:|---:|
| Cover title | 52-68 pt | 50 pt |
| Slide title | 36-44 pt | 35 pt |
| Section heading | 28-34 pt | 24 pt |
| Card title | 20-24 pt | 18 pt |
| Body | 16-20 pt | 16 pt |
| Footnote | 11-13 pt | 10 pt |
| KPI number | 42-64 pt | 36 pt |

### Diagram ratio

Each content slide should allocate at least 45% of the usable canvas to visuals:

- Diagram
- KPI cards
- Flow
- Timeline
- Comparison
- Architecture map
- Illustration placeholder
- Photo placeholder

Text-only slides are prohibited except a deliberate executive memo appendix, which is outside the main generated deck.

---

## Page 5. Narrative Model

ProposalPilot decks must follow a cumulative story. A standard sales proposal should follow this sequence:

1. Why now
2. What is the current friction
3. What changes after implementation
4. How the solution works
5. How value will be measured
6. How delivery progresses
7. What it costs
8. What decision is needed next

This mirrors consulting-style communication:

- Lead with the answer.
- Use grouped reasoning.
- Support with evidence.
- End with a decision or next action.

It also mirrors Amazon Working Backwards:

- Start from the customer outcome.
- Clarify the customer problem.
- Surface assumptions and dependencies.
- Answer economics and operational questions.

ProposalPilot must therefore avoid starting with "AI technology overview." It must start with the customer's business problem.

---

## Page 6. Required Page Types

The production engine must support these page types as first-class design units.

| Page type | Job | Core visual |
|---|---|---|
| Hero | Establish proposal quality and theme | Large title + key visual |
| Executive Summary | Give decision context | 3-point message board |
| Problem | Show friction or urgency | Issue cards / bottleneck map |
| Before / After | Show change | Split comparison / flow transition |
| Architecture | Explain how it works | Layered system diagram |
| Process | Show workflow | Step flow with icons |
| KPI Dashboard | Show value measurement | Metric cards + gauges |
| Timeline | Show plan | Roadmap / milestone lane |
| Estimate | Show commercial scope | Cost blocks / scope table |
| Risk & Mitigation | Reduce anxiety | Risk matrix |
| Comparison | Show alternatives | 2x2 / comparison table |
| Next Action | Ask for decision | CTA panel |
| Appendix | Preserve detail | Dense but controlled reference pages |

Every page type must have:

- Message template
- Visual layout template
- Icon rule
- Text length budget
- Required data inputs
- Fallback state when data is missing

---

## Page 7. Hero Page Rules

Hero pages decide whether the proposal feels premium within the first 5 seconds.

### Required elements

- Proposal title as a business outcome, not a technology label.
- Customer or project context.
- One key visual.
- ProposalPilot brand mark.
- Date / version / confidentiality marker if needed.

### Allowed visuals

- Abstract system visual
- Domain-specific illustration placeholder
- Photo placeholder
- Large icon composition
- Premium gradient panel

### Prohibited patterns

- Plain title on white background
- Dense subtitle
- Multiple CTAs
- Generic "Proposal" without category
- Web-production terms unless the project is actually web production

### ProposalPilot example

For AI-OCR:

Title: "AI-OCRで書類確認を短縮し、入力品質を標準化する"  
Key visual: document image placeholder + OCR scan frame + AI candidate chip

For manufacturing:

Title: "検査工程のばらつきをAIで見える化し、現場判断を揃える"  
Key visual: camera / product / anomaly detection overlay

---

## Page 8. Problem Page Rules

Problem pages must convert vague pain into structured business friction.

### Design pattern

- 3 issue cards
- Bottleneck flow
- "Why it matters" strip

### Required logic

Each issue card must include:

- Symptom
- Business impact
- Why current process struggles

### Visual elements

- Warning icon
- Process delay indicator
- Quality variance marker
- Workload meter

### Text budget

- Title: one conclusion sentence.
- Issue card: 1 short title + 1 short sentence.
- Bottom insight: 1 decisive sentence.

---

## Page 9. Before / After Rules

Before / After is one of the most important sales pages because it makes change tangible.

### Required layout

- Left: Current state
- Center: Transformation arrow / AI intervention
- Right: Future state
- Bottom: business impact

### Required comparison dimensions

Use 3-5 rows:

- Work step
- Human burden
- Quality control
- Data usage
- Time to output

### Avoid

- Before and After with identical layout and weak contrast
- Text-only comparison
- Overclaiming full automation when human review remains necessary

### ProposalPilot rule

If the solution includes AI, the After side should usually say:

- AI suggests
- Human verifies
- System records
- Team improves

This is safer and more credible than "AI fully automates everything."

---

## Page 10. Architecture Page Rules

Architecture pages must clarify, not intimidate.

### Required structure

Use layered architecture rather than a random network:

1. Input
2. AI / Analysis
3. Human Review
4. Integration
5. Data / Governance

### Visual elements

- Input icon
- AI icon
- Human icon
- API icon
- DB icon
- Security / audit icon

### Rules

- Use connectors behind nodes.
- Avoid crossing connectors.
- Limit primary nodes to 4-6.
- Use short labels.
- Put technical detail in appendix.

### Customer-facing wording

Say "既存業務へ段階連携" rather than "microservice API integration" unless the audience is technical.

---

## Page 11. KPI Dashboard Rules

KPI pages must make value measurable.

### Required visual

- 3-4 KPI cards
- Large number or target state
- Gauge, progress bar, sparkline, or delta arrow
- Confidence / measurement note

### KPI categories

- Time reduction
- Error reduction
- Quality standardization
- Cost visibility
- Throughput
- Review speed
- Adoption

### Rules

- If exact numbers are missing, do not invent them.
- Use "測定予定" or "目標設定対象" instead of fake values.
- Mark estimates as estimates.
- Make the number the visual hero.

### Example

Bad:

"作業時間を削減します"

Good:

"確認時間: PoCで測定 / 目標 20-30%短縮候補"

---

## Page 12. Timeline and Roadmap Rules

Timeline pages must reduce implementation anxiety.

### Required layouts

Choose based on project type:

- Linear timeline for short PoC
- Swimlane roadmap for multi-team projects
- Milestone cards for executive review
- Phase gate roadmap for large implementation

### Required fields

- Phase name
- Duration
- Main activity
- Output
- Decision point

### Recommended phases

1. 要件整理
2. データ確認
3. PoC構築
4. 現場検証
5. 本番化判断

### Rules

- Do not show a fake guaranteed schedule.
- Use ranges when dates are not confirmed.
- Show dependencies clearly.

---

## Page 13. Estimate Page Rules

Estimate pages must be commercially useful without overclaiming.

### Required visual

- Scope cards
- Estimate range or "individual estimate"
- Assumptions
- Exclusions
- Next action

### Rules

- Estimate line items must match proposal category.
- AI-OCR must not show Web production items such as CMS, SEO, sitemap, wireframe, or frontend implementation.
- Web projects may include CMS, SEO, sitemap, content migration, and design implementation.
- RPA may include process discovery, bot development, exception handling, monitoring, and training.
- CRM/SFA may include data migration, pipeline design, permission design, integration, and adoption support.

### Required disclaimer

"未確認の数量・範囲・連携条件は確定見積に含めません。"

---

## Page 14. Next Action Page Rules

Every proposal must end with a clear next action.

### Required elements

- Decision needed
- Who should act
- What material is needed
- When to meet next
- What will be delivered next

### Recommended layout

- Left: decision summary
- Right: next 3 actions
- Bottom: CTA bar

### Avoid

- Ending with "Thank you"
- Ending with cost table only
- Ending with a generic appendix

The final page should make it easy for the customer to say yes to the next small step.

---

## Page 15. Visual Components

ProposalPilot must use a consistent visual component library.

### Cards

- Radius: 16-20 px
- Padding: 24-32 px
- Border: 1 px slate-200 or blue-100
- Background: white, blue-50, slate-50
- Shadow: subtle, never heavy

### KPI cards

- Number top-left or center
- Unit visible
- Short label below
- Small trend chip
- Optional progress bar

### Icon cards

- 44-56 px icon container
- 1 icon per card
- Short title
- 1 sentence explanation

### Callout bars

- Use for one key implication.
- Max one per slide.
- Strong contrast.

### Tables

- Only when comparison is necessary.
- Max 5 columns.
- Use icons and chips to reduce text.

---

## Page 16. Icon System

Icons are mandatory in the premium engine.

### Required icon categories

| Concept | Icon direction |
|---|---|
| AI | Spark / neural node / processor |
| OCR | Document scan frame |
| Image recognition | Image frame + target |
| Human review | Person + check |
| API | Connector nodes |
| Database | Cylinder |
| Security | Shield |
| Audit log | Clipboard / history |
| Timeline | Flag / milestone |
| Cost | Yen / calculator |
| Risk | Alert triangle |
| Next action | Arrow / check circle |

### Style

- Line-based or filled-line hybrid.
- Consistent stroke width.
- Rounded endpoints.
- Navy/blue/cyan palette.
- No mixed icon libraries.

### Implementation rule

Use editable PowerPoint-native icon shapes where possible. If using SVG icons, embed them in a way that remains visually consistent and document the license.

---

## Page 17. Photo and Illustration Placeholders

Version38 must support image slots even when real images are unavailable.

### Why

Copilot, Gamma, Canva, and Beautiful.ai all raise perceived quality by adding visual material. ProposalPilot must not default to text-only slides.

### Placeholder types

- Customer process photo placeholder
- Product / document / machine image placeholder
- AI concept illustration placeholder
- Screenshot placeholder
- Before/After visual placeholder

### Rules

- Placeholder must be easy to replace in PowerPoint.
- Show a clear label such as "画像差し替え枠".
- Do not use fake customer photos.
- Do not invent real logos or customer visuals.
- If no image is available, use abstract editable shapes.

---

## Page 18. Color System

ProposalPilot's premium palette should balance trust and energy.

### Primary

- Deep Navy: `#07111F`
- Navy: `#0B1B35`
- Slate: `#334155`

### Secondary

- Blue: `#2563EB`
- Soft Blue: `#DBEAFE`
- Light Surface: `#F8FAFC`

### Accent

- Cyan: `#22D3EE`
- Aqua: `#A5F3FC`
- Green for success only: `#22C55E`
- Amber for caution only: `#F59E0B`
- Red for error only: `#EF4444`

### Gradients

Use gradients sparingly:

- Hero background
- KPI emphasis
- Section divider

Allowed gradient:

- Deep Navy -> Blue
- Blue -> Cyan
- Slate -> Deep Navy

Avoid:

- Purple-dominant gradients
- Beige-heavy palettes
- Decorative blobs without meaning

---

## Page 19. Typography System

### Font policy

- Japanese: Noto Sans JP, Yu Gothic fallback
- English: Inter, Aptos, or Arial fallback

### Hierarchy

| Role | Weight | Size |
|---|---|---:|
| Cover title | Bold | 56-68 |
| Slide assertion title | Bold | 36-44 |
| Section label | Bold | 13-15 |
| Card title | Bold | 20-24 |
| Body | Regular | 16-20 |
| KPI number | Bold | 44-64 |
| Caption | Regular | 11-13 |

### Rules

- No negative letter spacing.
- Do not scale font by viewport or slide width.
- Avoid long single-line Japanese text.
- For titles, use controlled line breaks.
- Body text should support the visual, not replace it.

---

## Page 20. Layout System

### Base canvas

- 16:9 wide
- 1280 x 720 px coordinate model

### Grid

- Outer margin: 64 px
- Main content frame: 1152 x 600 px
- 12-column grid optional
- Gutter: 24-32 px

### Layout families

1. Hero split
2. Full-bleed dark hero
3. 3-card issue grid
4. Before/After split
5. Layered architecture
6. KPI dashboard
7. Timeline lane
8. Estimate and CTA split
9. Roadmap staircase
10. Comparison table

### Rule

No two adjacent slides should use the same silhouette unless deliberately forming a sequence.

---

## Page 21. Competitive Difference

### Compared with Microsoft Copilot

Copilot is strong at creating and refining PowerPoint slides from prompts, files, and templates. It benefits from Microsoft 365 integration and organization templates.

ProposalPilot must differ by:

- Sales proposal domain logic
- Category-aware estimate and scope
- Quality Gate integration
- CRM / history / audit trail
- Proposal-specific KPI and risk pages
- Beautiful.ai handoff
- Organization / Workspace separation

### Compared with Gamma

Gamma is strong at fast, polished, web-native presentation generation and flexible card-based content.

ProposalPilot must differ by:

- Editable PowerPoint-first output
- Sales process integration
- Proposal category specificity
- Estimate integrity
- Compliance and audit
- Customer-ready sales workflow

### Compared with Beautiful.ai

Beautiful.ai is strong at smart slide layouts and visual polish after outline refinement.

ProposalPilot must differ by:

- Producing the business proposal logic before visual generation
- Feeding Beautiful.ai only high-quality prompt and structure
- Keeping PPTX/PDF/Beautiful.ai alternatives available
- Maintaining Quality Gate and revision history

### Compared with Canva

Canva is strong at brand kits, media, templates, and collaboration.

ProposalPilot must differ by:

- Sales-specific decision flow
- CRM-connected proposal history
- Role and workspace governance
- Category-specific quote logic
- Auditability

---

## Page 22. Consulting Deck Lessons

### McKinsey

McKinsey-style communication emphasizes structured thinking, single governing ideas, MECE grouping, and evidence-backed recommendations. ProposalPilot should adopt the logic, not copy the visual style.

Apply:

- Assertion titles
- Pyramid structure
- 3-part support
- Evidence-led exhibits
- Executive conclusion first

### BCG

BCG public materials often frame transformation around purpose, behaviors, levers, and implementation. ProposalPilot should turn abstract strategy into design levers and operating change.

Apply:

- Purpose -> lever -> behavior -> result
- Transformation stages
- Operating model diagrams

### Deloitte

Deloitte Insights emphasizes future-focused leaders, proprietary research, deep analysis, and actionable insights.

Apply:

- "What this means" callouts
- Insight + implication structure
- Executive-ready trend framing

### Accenture

Accenture Research emphasizes data-driven thought leadership, trend anticipation, and value from technology and human ingenuity.

Apply:

- Technology + business value pairing
- Research-style metric cards
- Transformation roadmap

### IBM Consulting

IBM IBV emphasizes trusted technology-based insights for smarter decisions and investments.

Apply:

- Trust and governance panels
- Technology decision framing
- Data-driven executive summary

---

## Page 23. ProposalPilot Unique Expressions

ProposalPilot can express things generic AI presentation tools cannot because it owns proposal workflow data.

1. Category-aware proposal structure.
2. Category-aware estimate items.
3. Quality Gate status embedded into output readiness.
4. Revision history as a visual timeline.
5. Proposal Optimization recommendations as cards.
6. Learning evidence summarized as anonymized patterns.
7. CRM status connected to proposal stage.
8. Beautiful.ai generation readiness and fallback.
9. Workspace/Organization context shown safely.
10. Human confirmation points shown as trust markers.

These expressions should become ProposalPilot's design signature.

---

## Page 24. Page Type Specification

### Hero

- Visual: large key image or abstract icon composition.
- Message: customer outcome.
- Required: title, subtitle, category, ProposalPilot mark.

### Problem

- Visual: issue cards or bottleneck flow.
- Message: current friction.
- Required: 3 issues, bottom implication.

### Before / After

- Visual: left/right flow.
- Message: what changes.
- Required: at least 3 comparison rows.

### Architecture

- Visual: layered diagram.
- Message: how the solution fits existing operations.
- Required: input, AI, human review, integration, data.

### KPI Dashboard

- Visual: 3-4 cards.
- Message: how value will be measured.
- Required: metric, current/target/measurement note.

### Timeline

- Visual: phase lane.
- Message: how implementation progresses.
- Required: 4-6 phases.

### Estimate

- Visual: scope cards + assumptions.
- Message: what is included and what must be confirmed.
- Required: scope, range or individual estimate, assumptions, next action.

### Next Action

- Visual: CTA panel.
- Message: the next decision.
- Required: action owner, required input, timing.

---

## Page 25. Generation Rules

The production engine must follow these generation rules.

### Content first

1. Classify proposal category.
2. Extract customer problem.
3. Generate narrative sequence.
4. Select page types.
5. Select visual layout.
6. Generate slide copy.
7. Generate editable shapes.
8. Validate overflow.
9. Validate category-specific terminology.

### Layout selection

Do not choose layout only by slide number. Choose by message type:

- Customer outcome -> Hero
- Pain point -> Problem
- Operational change -> Before/After
- System explanation -> Architecture
- Measurable value -> KPI Dashboard
- Implementation plan -> Timeline
- Commercial scope -> Estimate
- Decision request -> Next Action

### Fallback rules

If required data is missing:

- Do not invent numbers.
- Use "要確認" or "PoCで測定".
- Show assumption cards.
- Move unknowns into next action.

---

## Page 26. Quality Bar

A generated deck is not acceptable unless it passes these checks.

### Visual QA

- No text overflow.
- No broken relationships.
- No missing slide numbers.
- No missing ProposalPilot mark.
- No accidental external references.
- No garbled Japanese.
- No three identical layouts in a row.
- No body text below 16 pt.
- No title below 35 pt.
- No slide with only text.

### Business QA

- Category-specific vocabulary is correct.
- Estimate items match category.
- No web-production terms in non-web proposals.
- Next action is clear.
- Risks and assumptions are not hidden.
- Customer value is visible before technical detail.

### Sales QA

- The deck can be explained without reading every line.
- The customer can understand the value quickly.
- The proposal feels credible, not decorative.
- The design creates confidence.

---

## Page 27. Version 39 Implementation Scope

When implementation is approved, Version39 should not directly apply Prototype A or B as-is. It should implement this guideline as a design system.

### Expected implementation work

- Create a presentation design module.
- Define design tokens.
- Define page type templates.
- Define icon set.
- Define category-specific visual mapping.
- Add visual QA tests.
- Add category-specific PPTX regression tests.
- Add generated deck screenshots to QA artifacts.

### Files likely to change

Actual file names must be confirmed before implementation, but likely areas include:

- PPTX generation service
- Proposal profile/category logic
- Presentation visual theme module
- PPTX visual regression tests
- Documentation for presentation design QA

### Do not change without separate approval

- Frontend
- Backend API contracts
- DB schema
- Beautiful.ai API behavior
- Authentication and authorization

---

## Page 28. Final Design Principles

ProposalPilot Premium Design must obey these 12 principles.

1. Start with the customer's business outcome.
2. Use assertion titles.
3. Put one message on each page.
4. Turn text into structure.
5. Make value measurable.
6. Use editable PowerPoint-native objects.
7. Use icons consistently.
8. Use photo and illustration placeholders when real assets are missing.
9. Show human confirmation where AI decisions affect quality.
10. Do not invent data.
11. End with a concrete next action.
12. Make the customer feel the proposer is competent, careful, and worth trusting.

This is the target: not "a deck was generated," but "a salesperson can confidently take this into a customer meeting."

---

## Appendix A. Evaluation Rubric

| Category | 5 | 3 | 1 |
|---|---|---|---|
| Message clarity | One decisive claim | Topic is clear but not decisive | Unclear or multiple claims |
| Visual design | Visual carries the message | Visual supports text | Mostly text |
| Premium feel | Customer-ready | Internal-ready | Draft-like |
| Editability | Fully editable | Mostly editable | Rasterized or hard to edit |
| Category fit | Terminology matches | Some generic terms | Wrong category terms |
| Sales usefulness | Supports decision | Supports explanation | Decorative |
| Data integrity | No invented data | Some assumptions visible | Unsupported numbers |

---

## Appendix B. Version 38 Research Boundary

This Version 38.0 work is documentation only.

No changes were made to:

- Frontend
- Backend
- API
- DB
- Migration
- PPTX generation code
- Beautiful.ai integration
- Authentication
- Authorization

No commit or push is required for the research phase unless separately approved.

