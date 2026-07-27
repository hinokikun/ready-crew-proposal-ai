# Navigation Map

```mermaid
flowchart TD
  Login["SCR-001 Login"] --> Home["SCR-010 Home"]
  Home --> New["SCR-020 New Proposal"]
  New --> Prompt["SCR-030 Prompt Builder"]
  Prompt --> Questions["SCR-040 AI Questions"]
  Questions --> Strategy["SCR-050 Strategy Review"]
  Strategy --> Story["SCR-060 Story Review"]
  Story --> Outline["SCR-070 Slide Outline"]
  Outline --> Studio["SCR-080 Proposal Studio"]
  Studio --> Designer["SCR-090 Presentation Designer"]
  Designer --> Quality["SCR-100 Quality Check"]
  Quality --> Progress["SCR-110 Generation Progress"]
  Progress --> Complete["SCR-120 Generation Complete"]
  Complete --> PPTX["PPTX Export"]
  Complete --> PDF["PDF Export"]
  Complete --> Beautiful["Beautiful.ai Export"]
  Home --> History["SCR-130 Proposal History"]
  Home --> Projects["SCR-140 Project List"]
  Home --> Assistant["SCR-150 AI Sales Secretary"]
  Home --> Improvement["SCR-160 Business Improvement"]
  Home --> Analytics["SCR-170 Analytics"]
  Home --> Admin["SCR-180 Admin"]
  Home --> Settings["SCR-190 Settings"]
```

## Breadcrumb Examples

- Home / New Proposal / Prompt Builder / Confirm
- Home / Proposal History / Proposal Detail / Studio
- Home / Admin / Users
- Home / Settings / Workspace

## Current Implementation Mapping

| Future Node | Current Implementation |
|---|---|
| Home | `experienceView="home"` in AppShell |
| New Proposal | `experienceView="new-proposal"` + GuidedFlow + ProposalExperienceStudio |
| Proposal Studio | `experienceView="editor"` + ProposalExperienceStudio |
| Templates | `experienceView="templates"` + ProposalExperienceStudio Designer |
| History | CreationHistoryPanel |
| Admin | AdminSection and Admin panels |
| Settings | WorkspaceSwitcher, SystemDiagnosticsPanel |

