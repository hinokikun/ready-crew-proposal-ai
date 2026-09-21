# Rollback Drill Specification

Do not execute in PRE.

1. Set `PPTX_APPROVED_NATIVE_RENDERER_ENABLED=true` in an isolated test environment only.
2. Generate one Summary and one Detail test deck containing the eligible role and a blocked evidence role.
3. Inject or observe a controlled Native failure for the eligible role.
4. Confirm the same role is rendered by the existing renderer, the deck remains valid, and the failure trace is recorded.
5. Set the environment value to `false`.
6. Restart the backend.
7. Regenerate the same decks.
8. Confirm the existing renderer is restored, role order/count is unchanged, and no template or DB mutation occurred.

Expected result: one configuration change plus restart restores the current production path. No migration, API rollback, Frontend rollback, PDF rollback, or DB rollback is required.
