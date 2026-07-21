# Version52 Release Checklist

## Local

- [ ] `SALES_ASSISTANT_ENABLED=false` by default
- [ ] `SALES_ASSISTANT_PROPOSAL_ENABLED=false` by default
- [ ] `NEXT_PUBLIC_SALES_ASSISTANT_ENABLED=false` by default
- [ ] Backend `compileall` succeeds
- [ ] Backend full `pytest` succeeds
- [ ] Backend `pip check` succeeds
- [ ] Frontend `typecheck` succeeds
- [ ] Frontend `check:unused` succeeds
- [ ] Frontend `build` succeeds
- [ ] Frontend E2E succeeds
- [ ] `git diff --check` succeeds
- [ ] secret scan has no real API key, password, token, or DB URL value

## Regression

- [ ] login still works
- [ ] existing proposal generation still works
- [ ] existing PPTX generation is not modified
- [ ] existing PDF generation is not modified
- [ ] Strategy Engine fixtures still pass
- [ ] Sales Assistant generation still passes
- [ ] Proposal Preview still passes
- [ ] Feature Flag OFF states are safe
- [ ] member cannot access admin-only Sales Assistant APIs

## Cloud

- [ ] GitHub Actions latest commit is green
- [ ] Render deployment is live
- [ ] Vercel deployment is ready
- [ ] `/health` succeeds
- [ ] `/health/ready` succeeds
- [ ] cloud Feature Flags are intentionally configured
- [ ] admin validates Sales Assistant UI only when enabled
- [ ] no cloud check is marked successful until a human verifies it
