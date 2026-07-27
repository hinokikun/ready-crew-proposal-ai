# Migration Roadmap

DBは今すぐ変更しない。Version82以降で段階的に追加する。

## Order

1. Proposal core tables: proposals, proposal_versions.
2. Brief tables: proposal_briefs, strategy_briefs, story_plans.
3. Slide tables: slides, slide_elements.
4. Design tables: brand_kits, design_themes.
5. Job tables: generation_jobs, export_artifacts.
6. Quality tables: quality_reports, quality_findings.
7. Collaboration tables: comments, revisions, locks.
8. Knowledge extension: documents, chunks, citations.

## Safety Rules

- 既存tableを破壊的に変更しない。
- 追加columnはnullableまたはdefault付き。
- SQLiteとPostgreSQL両方で検証。
- 空DB migrationと既存DB migrationを確認。
- rollbackは原則`alembic downgrade`より`git revert + backup restore`を優先。

