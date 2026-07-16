# Changelog

All notable changes to AI営業秘書 are documented in this file.

## [1.0.0] - 2026-07-16

### Added

- Product-ready README for GitHub top page
- Version 1.0 release notes
- Production support, contribution, conduct, and security documents
- Demo data for safe browser/UAT verification
- Documentation archive for older version-specific handoff files
- ProposalPilot Pilot Fold final candidate logo, icon, favicon, and OGP export assets

### Changed

- Organized product documentation for limited customer release
- Clarified admin guide, user guide, environment variables, FAQ, support, and security reporting
- Moved old version-specific documents into `docs/archive/`
- Clarified login fallback wording so unexpected authentication failures remain readable in Japanese

### Fixed

- Preserved the latest user-entered proposal input through analysis so AI-OCR projects are not replaced by previous Web project content
- Prevented previous proposal details from leaking into a newly started proposal
- Removed the fixed Web-site fallback behavior from the proposal analysis flow

### Security

- Confirmed MIT license presence
- Added vulnerability reporting instructions
- Reconfirmed that secrets, API keys, passwords, tokens, customer body text, and generated full text must not be committed or logged

## [1.0.0-rc1] - 2026-07-15

### Changed

- Eliminated release blockers around production CORS, security headers, Japanese text quality, release gate, UAT, and runbook documentation
- Added Version 25 RC1 release candidate audit

### Verification

- Backend pytest: 167 passed
- Frontend E2E: 42 passed
- Typecheck, build, compileall, pip check, and git diff checks passed locally
