# Changelog

All notable changes to Ready Crew Proposal AI are documented in this file.

## [2.2.0-rc] - 2026-07-30

### Added

- Customer Ready content remediation for 20 real project cases.
- Release evidence package with PPTX, PDF, PNG, validation reports, and before/after summaries.
- Production release notes, deployment guide, user guide, admin guide, architecture diagram, known issues, and OSS license inventory.

### Changed

- Unified release documentation around Version 2.2 production readiness.
- Clarified that real customer submission still requires final human confirmation of customer-specific facts.
- Restored detailed PPTX output to the existing 20 to 25 page contract.

### Verified

- Backend pytest: 518 passed.
- Frontend Playwright E2E: 75 passed.
- Frontend typecheck and build passed.
- 20 / 20 remediated real project cases reached CUSTOMER_READY.
- 20 / 20 PPTX files were converted to PDF and PNG with LibreOffice and Poppler.

## [2.1.0] - 2026-07

### Added

- Proposal Validation Engine.
- Multi-persona proposal review.
- Proposal benchmark scoring.
- Red-team review.
- Acceptance Score and Customer Ready judgement.
- Customer question simulator.
- Slide-by-slide review and Visual QA++.
- Golden validation suite expansion.

## [2.0.0] - 2026-07

### Added

- AI Sales Consultant Engine.
- Customer, industry, decision maker, business issue, competitive strategy, win strategy, ROI, roadmap, objection, and proposal review analysis.
- Internal strategy-first proposal flow.

## [1.2.0] - 2026-07

### Changed

- Upgraded proposal output toward customer-ready sales material.
- Improved executive summary, story, KPI, estimate, Beautiful.ai prompt, and submission review quality.
- Strengthened PowerPoint design direction and category-aware proposal content.

## [1.1.0] - 2026-07

### Changed

- Improved proposal quality and PowerPoint design.
- Reduced bullet-heavy pages.
- Added stronger story flow, comparison, KPI, schedule, estimate, and pre-submission review structure.

## [1.0.0] - 2026-07-16

### Added

- Product-ready README and Version 1.0 release notes.
- Production support, contribution, conduct, and security documents.
- Demo data for browser and UAT verification.
- ProposalPilot brand assets and release documents.

### Fixed

- Prevented newly entered AI-OCR projects from being replaced by previous Web project content.
- Removed fixed Web-site fallback behavior from proposal analysis.
- Preserved latest project input through analysis and review.

## [1.0.0-rc1] - 2026-07-15

### Verified

- Backend pytest passed.
- Frontend E2E passed.
- Typecheck, build, compileall, pip check, and git diff checks passed locally.
