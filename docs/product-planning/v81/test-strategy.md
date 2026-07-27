# Test Strategy

## Pyramid

- Unit: pure rules, schema validation, mappers.
- Schema: AI JSON contracts.
- Service: Strategy, Story, PPTX, Beautiful.ai.
- API: auth, roles, workspace, proposal, export.
- Database: migration, constraints, scoping.
- Integration: Proposal -> Quality -> Export.
- PPTX Output: structure snapshot, text search, relationship.
- Visual Regression: rendered slide screenshots.
- E2E: login, guided flow, V80 navigation, Beautiful.ai, export.
- Accessibility: keyboard, aria, contrast.
- Performance: large input, long history.
- Security: auth, object access, injection.
- AI Offline Evaluation: golden fixtures.

## Required Fixtures

Webリニューアル、EC改善、採用サイト、AI導入、DX、新規事業、情報不足、情報過多、予算未定、経営者向け、営業担当向け、長い日本語、不正入力、Prompt Injection、外部API失敗。

## Rule

外部APIを呼ぶテストではモックを使用する。テストを通すために機能を無効化しない。

