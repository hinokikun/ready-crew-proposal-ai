# Design System Migration Inventory + UI Contract Freeze

基準: `design-refresh` / `8f7dc92`  
監査方式: frontendの静的READ-ONLY監査  
対象: 利用者画面、Manager画面、管理画面、共通UI、global CSS、frontend E2E selector  
対象外: Production、Render/Vercel、Feature Flag、OpenAI API、Presentation Master、M30、renderer関連

## 1. UI Contract Freeze

### LEVEL 1 — FROZEN FUNCTIONAL CONTRACT

以下は視覚刷新のために変更しない。見た目を変更する場合も、DOM上の契約を保持する。

| 契約 | 凍結内容 | 確認箇所 |
|---|---|---|
| Test hook | `data-testid`の値、対象要素、存在条件 | `frontend/components/**/*.tsx`, `frontend/e2e/*.spec.ts` |
| Accessibility role | `alert`, `dialog`, `status`, `progressbar`, `button`, `heading`, `link`, `textbox`等 | 各component、E2E |
| Accessible name | button名、heading名、link名、label名 | E2Eの`getByRole` / `getByLabel` |
| ARIA | `aria-label`、`aria-current`、`aria-expanded`、`aria-modal`、`aria-live`、`aria-valuenow` | Nav、Modal、Progress、Status |
| Panel identity | `admin-*-panel`、`creation-history-panel`等のid | AdminSection、CreationHistoryPanel、E2E |
| Navigation state | `ProposalExperienceView`の値、active state、role別表示条件、sidebar open/collapsed | `ProposalExperienceNav.tsx`, `AppShell.tsx` |
| API boundary | API callの発火条件、single-shot条件、payload、retry条件、response反映条件 | `AppShell.tsx`, `frontend/client-api/*` |
| Permission gating | user / manager / adminの表示・操作権限、Quality Gate、maintenance条件 | `lib/roles.ts`, `AppShell.tsx` |
| Proposal flow | 入力→整理→生成→確認→Quality Gate→出力の順序 | `GuidedFlow.tsx`, `AppShell.tsx` |
| Output behavior | PPTX/PDF/Beautiful.ai等のdownload、busy lock、retry、quality unlock | GuidedFlow、AppShell |
| State behavior | loading中disabled、error retry、success表示、empty表示の発火条件 | UI各component、E2E |

### LEVEL 2 — MIGRATION COMPATIBILITY LAYER

段階移行中は既存classを削除せず、将来componentのclassまたはCSS tokenへaliasする。

| 既存class群 | 扱い |
|---|---|
| `.primary-button`, `.secondary-button`, `.danger-button`, `.text-button`, `.icon-button` | Button / IconButtonのcompatibility aliasとして維持 |
| `.v80-*`, `.v81-*` | App Shell、sidebar、studio、既存E2Eのselectorとして維持 |
| `.advanced-foldout`, `.analysis-foldout` | Panel / Disclosureへ段階移行。summaryとidは維持 |
| `.field`, `.field-grid`, `.easy-field-grid`, `.estimate-field-grid` | Field / FormLayoutへ段階移行 |
| `*-card`, `*-panel`, `*-grid` | Card / Panel / Grid primitivesへ段階移行 |
| `.status-note`, `.status-message-*`, `.decision-pill`, `.status-pill` | Status / Alert / Badgeへ段階移行 |
| `.table-scroll`, `.usage-dashboard-table` | Table wrapper / DataTableへ段階移行 |
| `.skeleton-*`, `.pp-spinner`, `.pp-progress` | Loading primitivesへ統合 |

### LEVEL 3 — REDESIGNABLE VISUAL LAYER

機能契約を保持する限り、以下は再設計可能。

- color、surface、border、typography、line-height
- spacing、余白、grid密度、container幅
- radius、shadow、elevation
- icon size、icon treatment、装飾
- card / panel / table / buttonの外観
- active / hover / focus-visibleの視覚表現
- responsive時のstacking、余白、表示密度
- 利用者画面と管理画面の情報階層・見出し階層

## 2. Migration Inventory

| Semantic role | 現行component / class | 使用画面 | 対象role | 主なstate | test / ARIA / name / id | E2E | Functional contract | Visual redesign | 将来component |
|---|---|---|---|---|---|---|---|---|---|
| Authentication entry | `AuthGate`, `.auth-shell`, `.auth-card`, `.auth-mode-card` | login | user / manager / admin | default, active mode, error, loading | `login-mode-user`, `login-mode-admin`, `login-submit`; labels: メールアドレス、アクセスパスワード | Yes | login mode、credentials、submit、error条件 | Yes | `AuthCard`, `SegmentedChoice`, `Field`, `Button` |
| Global header | `Header`, `.workspace-header`, `.header-actions`, `.status-pill` | 全認証後画面 | all | normal, presentation, dark, logout | button names: 発表モード、ダークモード、ログアウト | Yes | header actions、mode state、logout | Yes | `Header`, `HeaderAction`, `Status` |
| Workspace context | `WorkspaceSwitcher`, `.workspace-context-card` | 全認証後画面 | all | loaded, loading, error, empty available list | `aria-label="現在のOrganizationとWorkspace"`; select; refresh button | Yes/indirect | workspace switch API、refresh、current context | Yes | `WorkspaceSwitcher`, `Select`, `InlineAlert` |
| Primary navigation | `ProposalExperienceNav`, `.v80-sidebar`, `.v80-nav-item` | 全認証後画面 | role-filtered | active, collapsed, mobile open, backdrop | `v80-sidebar`, `nav-*`; `aria-current`, `aria-label="メインメニュー"` | Yes | view id、role filtering、open/collapse、mobile close | Yes, DOM contract frozen | `Sidebar`, `NavigationItem`, `MobileDrawer` |
| Page identity | AppShell `.v80-page-intro`, `.eyebrow` | home以外の各view | all | normal, detail mode | `aria-label="現在の画面"`; heading accessible names | Yes | view title/description、detail toggle条件 | Yes | `PageHeader`, `ModeToggle` |
| User home | `UserHomePanel`, `.user-home-*` | ホーム | user / manager / admin | empty, recent history, current proposal, generating | `user-home-panel`; headings and CTA names | Yes | resume/new/history/analytics navigation | Yes | `HomeDashboard`, `QuickAction`, `RecentList` |
| Proposal source input | `GuidedFlow`, `.guided-*`, `.wizard-*` | 提案書を作る | user / manager / admin | empty, typing, sample, organizing, error | `guided-flow`, `project-source-input`; label/heading; CTA AIで提案書を作成 | Yes | source state、minimum input、generate conditions | Yes | `ProposalInput`, `Textarea`, `InputModeTabs` |
| Proposal step navigation | `StepNavigation`, `.guided-step-nav`, `.guided-step-pill` | 提案作成 | all allowed users | active, completed, locked | step labels and buttons | Yes | step order、current step、allowed transition | Limited: visual only | `Stepper`, `ProposalStep` |
| Pre-generation review | GuidedFlow / AppShell `.check-panel`, `.plan-panel`, `.hearing-panel`, `.deal-panel` | 提案作成 | all allowed users | incomplete, warning, ready | aria labels: 入力内容チェック、提案前プラン、ヒアリングシート、案件ランク判定 | Yes/indirect | required inputs、review gate、calculation display | Yes | `ReviewSummary`, `Warning`, `ScoreCard` |
| Generation CTA | GuidedFlow / AppShell `.primary-button`, `.generate-flow-panel` | 提案作成 | allowed users | enabled, disabled, loading, error, retry | accessible names: AIで提案書を作成、提案書を生成、生成開始 | Yes | API call condition、single-flight、loading disabled | Yes | `Button`, `AsyncAction`, `Progress` |
| AI progress | `WorkspaceProgress`, `AgentProgress`, `.wizard-progress-flow`, `.pp-progress` | 提案作成、AI支援 | all allowed users | idle, running, completed, failed | `role=progressbar`, `role=status`; progress labels | Yes/indirect | stage progression、busy state | Yes | `Progress`, `AgentTimeline`, `Stepper` |
| Result review | GuidedFlow / `AiWorkspacePanel`, `.workspace-human-review-card`, `.guided-quality-*` | 提案結果 | manager / admin and allowed users | pending, confirmed, error | Human Review labels, quality test ids | Yes | human review and result confirmation | Yes | `ReviewPanel`, `Status`, `ActionBar` |
| Quality Gate | `AiWorkspacePanel`, GuidedFlow, `.workspace-quality-gate-card`, `guided-quality-check` | 提案結果 / output | allowed users, admin bypass | incomplete, saving, complete, bypassed | `guided-quality-check`; button 提出前チェックを完了する | Yes | completion, bypass permission, download unlock | Yes, controls frozen | `QualityGate`, `Checklist`, `DangerAction` |
| Output panel | GuidedFlow / proposal output components | 提案結果 | allowed users | locked, ready, downloading, error, retry | PowerPoint/PDF/Beautiful.ai button names and test ids | Yes | download behavior、quality unlock、busy lock | Yes | `OutputPanel`, `DownloadButton`, `ExportStatus` |
| History | `CreationHistoryPanel`, `.workspace-history-list`, `#creation-history-panel` | 作成履歴、分析 | all | empty, loading, loaded, error | panel id and heading 作成履歴 | Yes | history load、resume、CSV behavior | Yes | `HistoryPanel`, `DataList`, `EmptyState` |
| CRM / projects | `CrmPanel`, `.v80-view-panel` | 案件管理 | manager / admin | empty, loading, loaded, error | project navigation names | Indirect | CRM API、project status transition | Yes | `ProjectTable`, `ProjectCard`, `StatusBadge` |
| AI support | `ProposalAgentDashboard`, copilot components | AI支援 | manager / admin | empty, loading, generating, error, success | heading AI営業アシスタント、CTA names | Yes | assistant API、output and CRM handoff | Yes | `AssistantWorkspace`, `RecommendationList` |
| Detail studio | `ProposalExperienceStudio`, `.v80-studio`, `.v80-*` | 詳細編集、出力設定 | manager / admin | no result, editing, generating, ready | `v80-proposal-studio`, `v80-presentation-designer`, `v80-slide-editor` | Out of scope contract audit | view and output behavior frozen; visual redesign deferred | Limited | `StudioShell`, `EditorLayout` |
| Analytics | `RealOperationsDashboard`, dashboard components | 管理分析、分析・レポート | manager / admin or user improvement | empty, loading, loaded, error | KPI headings, table selectors | Yes | metrics source、CSV、navigation | Yes | `AnalyticsDashboard`, `KpiGrid`, `DataTable` |
| Admin console | `AdminSection`, `.admin-menu-foldout`, `#admin-menu-panel` | 管理コンソール | admin | closed, open, loading, permission, error | `admin-menu`; summary 管理コンソールを開く | Yes | admin permission、open state、panel identities | Yes, structure staged | `AdminSection`, `AdminNavigation`, `DisclosureGroup` |
| Admin readiness | AdminSection `.trial-check-panel`, `.trial-check-grid` | 管理コンソール | admin | ready, alert, unknown | aria label 管理者ダッシュボード | Indirect | readiness data and health status | Yes | `ReadinessGrid`, `StatusCard` |
| Admin data panels | AdminUsers, Usage, Analytics, Audit, Feedback components | 管理コンソール | admin | loading, empty, loaded, error, action busy | panel ids where present; tables and action names | Yes | CRUD, audit, CSV, API call conditions | Yes | `AdminPanel`, `DataTable`, `ActionBar` |
| Admin diagnostics | HealthStatus, SystemDiagnostics, ExternalIntegrations | 管理コンソール / UAT | admin | checking, ok, warning, error | `role=alert/status`, diagnostic test ids | Yes | diagnostic calls, permission and read-only behavior | Yes | `DiagnosticsPanel`, `StatusSummary` |
| Forms | labels with `.field`, inputs/selects/textarea | 全画面 | all by permission | default, focus, invalid, disabled, loading | label accessible names; select IDs where used | Yes | label association、validation、submit conditions | Yes | `Field`, `Select`, `Textarea`, `Checkbox` |
| Tables | `.usage-dashboard-table`, `.table-scroll` | admin, analytics, history | manager / admin | empty, loading, overflow, row action | table semantics, headings, scoped button names | Yes | data ordering、row actions、download | Yes | `Table`, `DataTable`, `TableScroll` |
| Modal / confirmation | AppShell `.confirm-overlay`, `.pilot-checklist-overlay`, tutorial overlay | onboarding、confirm、pilot | role-dependent | open, close, submitting, error | `role=dialog`, `aria-modal=true`, labels 操作ガイド / 作成前確認 | Yes | open/close、confirmation、blocking condition | Yes, dialog contract frozen | `Modal`, `ConfirmDialog` |
| Inline status | `StatusMessage`, `.status-note`, banners | 全画面 | all | info, success, error, warning | `role=status` or `role=alert` | Yes/indirect | message timing and error/retry behavior | Yes | `Status`, `Alert`, `Toast` |
| Empty/loading primitives | `EmptyState`, `Skeleton`, `Spinner` | 全画面 | all | empty, skeleton, loading | `aria-label`, `role=status`, `aria-hidden` | Indirect | loading/empty existence conditions | Yes | `EmptyState`, `Skeleton`, `Spinner` |

## 3. State Matrix

| State | 現行表現 | 凍結する挙動 | 再設計可能な範囲 |
|---|---|---|---|
| Normal | card、panel、button、text | 表示条件と操作可能性 | surface、type、spacing、density |
| Hover | CSS hover | API・navigationを発火させないこと | color、elevation、motion |
| Active | `.is-active`、`aria-current`、selected class | active view、selected value | indicator、background、border |
| Disabled | native `disabled`、権限・gate・maintenance条件 | disabled条件、button name、busy lock | contrast、cursor、説明表示 |
| Loading | Spinner、Skeleton、Loader2、inline message | call中の二重送信防止、disabled | animation、layout reservation |
| Error | `role=alert`、status note、retry/reload | error発火、retry対象、API再試行 | tone、icon、layout |
| Success | status message、badge、completion card | completion state、unlock state | emphasis、icon、summary layout |
| Empty | `EmptyState`または画面別empty text | empty condition、CTA有無 | illustration、copy hierarchy、spacing |

## 4. Design System Foundations

| Foundation | 現行 | 将来仕様候補 | Migration方針 |
|---|---|---|---|
| Color | `--pp-*`、semantic vars、cafe compatibility alias、hard-coded values | semantic role color: background/surface/text/brand/info/success/warning/danger/focus | 既存varをalias化し、画面ごとの直書きを段階削減 |
| Typography | `--font-sans`、global heading、`.eyebrow`、個別font-size | display / h1 / h2 / h3 / body / label / caption / mono | accessible nameと文言を維持して視覚scaleを統一 |
| Spacing | 個別px、gap、padding、margin | 4pxまたは8px基準のspacing scale | 既存値を壊さずtokenへ置換 |
| Radius | `--radius-xs`〜`xl`と個別値 | control / card / panel / modal / pill | visual-onlyで置換 |
| Shadow | `--shadow-*`と個別box-shadow | none / subtle / raised / overlay | elevation semanticsに集約 |
| Motion | `--transition-*`、個別animation、reduced motion | duration/easing、reduced-motion contract | state timingは維持し、表現のみ統一 |
| Breakpoints | 560/640/720/760/900/1024/1080等 | container-first + 3〜4 responsive tiers | 既存viewport動作を確認しながら統合 |

## 5. Design System Primitives

| 将来component | 現行mapping | 凍結事項 |
|---|---|---|
| Button | `.primary-button`, `.secondary-button`, `.danger-button`, `ui/Button` | accessible name、disabled、loading、onClick条件 |
| IconButton | `.icon-button` | `aria-label`、title、target action |
| Field | `.field`, label + input | label/name、validation、value binding |
| Select | native select、workspace select、relationship select | option value、label、selected state |
| Textarea | source / memo / comment textarea | label、input value、submit条件 |
| Checkbox | purpose / checklist checkbox | checked value、completion semantics |
| Card | `*-card`, `ui/Card` | semantic grouping、heading、test hook |
| Panel | `*-panel`, `.advanced-foldout` | panel id、open state、ARIA |
| SectionHeader | `.section-heading`, `.panel-heading` | heading text、supporting copy |
| Badge | `.decision-pill`, `.status-pill`, `ui/StatusBadge` | status value、accessible text |
| Status | `.status-note`, `ui/StatusMessage` | role、tone、message timing |
| Alert | `.warning-box`, banners, `role=alert` | severity、blocking condition |
| EmptyState | `ui/EmptyState`, `*-empty` | empty condition、optional action |
| Skeleton | `ui/Skeleton`, `.skeleton-*` | loading existence、layout reservation |
| Spinner | `ui/Spinner`, Loader2 | `role=status`、loading label |
| Progress | `ui/Progress`, WorkspaceProgress | value、label、completion state |
| Modal | `.confirm-overlay`, pilot/tutorial overlays | `role=dialog`, `aria-modal`, close/submit |
| Drawer | mobile sidebar/backdrop | open state、navigation selection、focus behavior |
| Table | `.usage-dashboard-table`, `.table-scroll` | columns、row actions、ordering、overflow |
| Tabs | input mode tabs、studio tabs | selected value、accessible tab semantics |
| Stepper | guided step pills / progress | step order、active/completed/locked state |

## 6. Design System Patterns

| 将来pattern | 現行mapping | Migration boundary |
|---|---|---|
| AppShell | `AppShell.tsx`, `.app-shell`, `.v80-experience-shell` | state、view values、API、permissionは変更禁止。外観のみ段階移行 |
| Sidebar | `ProposalExperienceNav`, `.v80-sidebar` | nav item id、role filter、active state、mobile behaviorは凍結 |
| Header | `Header`, `.workspace-header` | action accessible name、mode/logout behaviorは凍結 |
| PageHeader | `.v80-page-intro`, `.section-heading` | view title/descriptionを維持 |
| WorkspaceSwitcher | `WorkspaceSwitcher` | current context、switch API、refresh/error behaviorを維持 |
| ProposalStep | `GuidedFlow`, `StepNavigation`, guided step cards | step order、CTA、draft persistenceを維持 |
| QualityGate | `AiWorkspacePanel`, guided quality sections | completion、bypass、download unlockを維持 |
| OutputPanel | GuidedFlow output sections、download handlers | output format、busy、retry、unlockを維持 |
| AdminSection | `AdminSection`, nested `details` | panel ids、permission、data loading/action conditionsを維持 |
| AdminDangerZone | delete, bypass, maintenance, retention actions | confirmation、permission、danger accessible nameを維持 |

## 7. E2E Contract Register

静的調査で、`frontend/e2e` 2ファイルから以下を確認した。

- unique `data-testid` references: **59**
- unique `getByLabel` references: **19**
- role category: alert / button / heading / link / textbox
- panel/id locator references: **13**（summary locatorを含む）
- component側の概数: `data-testid` 81、`role` 59、`aria-label` 188、`id` 134

Presentation Master / M30 / renderer関連のselectorは、このmigration inventoryの機能対象から除外し、今後も別契約として扱う。

### Highest-risk contracts

1. `v80-sidebar`、`nav-*`、`aria-current`、`ProposalExperienceView`
2. `guided-flow`、`project-source-input`、proposal CTA、step order
3. `guided-quality-check`、Quality Gate completion / bypass / download unlock
4. `admin-menu`、`admin-menu-panel`、nested admin panel ids
5. login test ids、form labels、button accessible names
6. `role=dialog`、`aria-modal`、pilot/tutorial/confirm overlay existence
7. loading中のdisabled、single-flight、retry buttonの存在条件
8. tablesのcolumn/row action semanticsと`.table-scroll`

## 8. Safe Visual Change Areas

- token valuesの変更とsemantic alias追加
- heading hierarchy、font size、line-height、letter spacing
- panel/card/buttonのsurface、border、radius、shadow
- spacingとlayout density
- hover/focus-visible/disabledの視覚表現
- sidebarのvisual grouping（DOM順・nav idは維持）
- mobileの余白、grid stacking、overflow表現
- table header、row height、zebra、横スクロールUI
- loading skeletonの形状とanimation（loading条件は維持）
- admin category headingとpanel visual hierarchy

## 9. Non-negotiable Rules for Future Design Work

- `AppShell.tsx`の機能ロジック、API条件、state名、permission条件を変更しない。
- `data-testid`、role、ARIA、accessible name、panel idを変更しない。
- Proposal step順、CTAの発火条件、download/output behaviorを変更しない。
- 既存classは、移行完了までcompatibility aliasとして残す。
- visual changeとfunctional changeを同じcommit/タスクに混在させない。
- E2Eが参照する文言を変更する場合は、先に契約変更として明示承認を得る。
- Presentation Master / M30 / renderer関連は別監査・別契約で扱う。

## 10. Audit Record

- Existing code changed: NO
- Existing CSS changed: NO
- Tests changed: NO
- Production changed: NO
- OpenAI API used: NO
- Render/Vercel changed: NO
- Feature flags changed: NO
