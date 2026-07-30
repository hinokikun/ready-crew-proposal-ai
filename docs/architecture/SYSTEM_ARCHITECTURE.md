# System Architecture

## Overview

Ready Crew Proposal AI is a browser-based proposal creation service. The Frontend provides a guided workflow for sales users. The Backend handles authentication, workspace separation, AI proposal generation, quality validation, and output generation.

## High-Level Flow

```mermaid
flowchart TD
    U["Sales User / Admin"] --> FE["Frontend<br/>Next.js / React / Vercel"]
    FE --> API["Backend API<br/>FastAPI / Render"]
    API --> AUTH["Auth / Role / Organization / Workspace"]
    API --> DB["Database<br/>SQLite local / PostgreSQL production"]
    API --> AI["AI Layer<br/>OpenAI / Mock AI"]
    AI --> STRATEGY["AI Sales Consultant<br/>Customer / Industry / Decision / Win Strategy"]
    STRATEGY --> PROPOSAL["Proposal Generator<br/>Story / Estimate / KPI / Slides"]
    PROPOSAL --> VALIDATION["Customer Ready Gate<br/>Proposal Validation / Quality Report"]
    VALIDATION --> PPTX["PPTX Generator"]
    VALIDATION --> PDF["PDF Estimate Generator"]
    VALIDATION --> BAI["Beautiful.ai Integration"]
    API --> HISTORY["History / Audit / Diagnostics"]
```

## Runtime Components

| Component | Responsibility |
|---|---|
| Frontend | Login, guided proposal flow, result review, history, admin screens |
| Backend API | Request validation, authentication, authorization, service orchestration |
| Auth | Login, token status, role enforcement |
| Workspace | Organization and workspace scoped data |
| AI Services | OpenAI-backed or mock proposal generation |
| AI Sales Consultant | Internal strategy analysis before proposal output |
| Proposal Generator | Proposal content, slide data, estimate data |
| Customer Ready Gate | READY / REVIEW_REQUIRED / NOT_READY judgement |
| Proposal Validation | Multi-perspective proposal quality review |
| PPTX Generator | PowerPoint output |
| PDF Generator | Estimate PDF output |
| Beautiful.ai Service | Prompt API payload and URL handling |
| Diagnostics | Backend, DB, OpenAI, Beautiful.ai, auth, and frontend URL checks |

## Frontend to Backend

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Backend
    participant AI
    participant Output

    User->>Frontend: Paste project information
    Frontend->>Backend: POST /api/analyze
    Backend->>AI: Build proposal and strategy
    AI-->>Backend: Proposal data
    Backend-->>Frontend: Analysis, slides, estimate, quality data
    User->>Frontend: Complete customer-ready checks
    Frontend->>Backend: POST /api/download-pptx or PDF / Beautiful.ai
    Backend->>Output: Generate file or Beautiful.ai presentation
    Output-->>Backend: File bytes or returned URL
    Backend-->>Frontend: Download or URL response
```

## Backend Modules

```mermaid
flowchart LR
    Main["app.main"] --> Routers["app.routers"]
    Main --> Services["app.services"]
    Services --> Proposal["openai_service / pptx_service / pdf_service"]
    Services --> Quality["customer_ready_quality / proposal_validation_engine"]
    Services --> Beautiful["beautiful_ai_service"]
    Services --> Strategy["sales_consultant_engine"]
    Routers --> Auth["auth / users / workspace"]
    Routers --> System["system diagnostics"]
    Routers --> Validation["proposal_validation"]
```

## AI Composition

```mermaid
flowchart TD
    Input["Project Input"] --> Normalize["Input normalization"]
    Normalize --> Consultant["AI Sales Consultant"]
    Consultant --> Analysis["Proposal Analysis"]
    Analysis --> Slides["Slide Data"]
    Slides --> Quality["Customer Ready + Proposal Validation"]
    Quality --> Outputs["PPTX / PDF / Beautiful.ai"]
```

## Beautiful.ai Boundary

```mermaid
flowchart TD
    Proposal["Proposal Data"] --> Mapper["Beautiful.ai Payload Mapper"]
    Mapper --> API["Beautiful.ai API"]
    API --> Response["API Response"]
    Response --> URL["Use editor_url first, then player_url"]
    URL --> Frontend["Open returned URL only"]
```

The application must not generate Beautiful.ai editor URLs from `presentation_id` alone. It should use URLs returned by the Beautiful.ai API.

## Production Boundary

| Area | Production Rule |
|---|---|
| Secrets | Stored only in Render or Vercel environment variables |
| Database | PostgreSQL recommended |
| CORS | Allow production frontend URL only, plus required local origins for development |
| Feature Flags | Backend is the source of truth |
| Logs | Do not output API keys, passwords, tokens, or customer secrets |
| Rollback | Render previous deployment + Vercel previous deployment |

## Related Documents

- [Version 2.2 Release Notes](../releases/VERSION_2.2_RELEASE.md)
- [Production Deployment Guide](../deployment/PRODUCTION_DEPLOYMENT.md)
- [Administrator Guide](../manual/ADMIN_GUIDE.md)
