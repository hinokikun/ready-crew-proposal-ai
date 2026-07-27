# API Inventory

調査時点で`backend/app/routers`は27ファイル、`@router` route handlerは158件。

## Current API Groups

| Group | Current Prefix | Status | Notes |
|---|---|---|---|
| Auth | `/api/auth` | implemented | login/status/logout |
| Users | `/api/users` | implemented | admin user management, password |
| Organizations | `/api/organizations` | implemented | context, workspace, membership |
| Workspace | `/api/workspace` | implemented | conversations, summary |
| Projects | `/api/projects` | implemented | CRM, lifecycle, outcome |
| Logs | `/api/logs` | implemented | usage, audit, history, business improvement |
| Admin Observability | `/api/admin` | implemented | history stats, CSV |
| Beautiful.ai | `/api/beautiful-ai` | implemented | status, presentations, diagnostics |
| System | `/api/system` | implemented | diagnostics, environment |
| Sales Assistant | `/api/sales-assistant` | partial | Feature Flag, preview, export |
| Proposal Agent | `/api/proposal-agent` | partial | dashboard, memory |
| Quality Gates | `/api/quality-gates` | implemented | get/create/complete/bypass |
| Presentation Review | `/api/presentation-review` | implemented | reviews, revisions |
| Proposal Optimization | `/api/proposal-optimization` | implemented | recommendations, backlog |
| Knowledge | `/api/knowledge` | partial | entries/search/templates |
| Learning | `/api/learning` | partial | dashboard/run |
| Prompts | `/api/prompts` | partial | versions/experiments |
| Analytics | `/api/analytics` | implemented | events/dashboard/errors |
| Pilot | `/api/pilot` | implemented | UAT and maintenance |
| Releases | `/api/releases` | implemented | release records |

## Deprecated Candidates

まだ廃止しない。重複するDashboard系APIはVersion85で整理候補。

