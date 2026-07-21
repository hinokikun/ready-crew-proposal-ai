# Version52 Deployment Guide

## Environment Variables

Keep defaults unless intentionally validating the RC path.

```env
SALES_ASSISTANT_ENABLED=false
SALES_ASSISTANT_PROPOSAL_ENABLED=false
NEXT_PUBLIC_SALES_ASSISTANT_ENABLED=false
PRESENTATION_ENGINE_MODE=legacy
```

## Controlled RC Enablement

1. Enable backend Sales Assistant.
2. Enable frontend Sales Assistant UI.
3. Validate admin-only access.
4. Enable Proposal Preview only after Sales Assistant generation is verified.
5. Keep PPTX and Beautiful.ai disconnected from this path.

## Cloud Verification

- Render: deployment live, `/health`, `/health/ready`
- Vercel: deployment ready, latest commit
- GitHub Actions: latest workflow green

Do not mark cloud checks as successful without direct human confirmation.
