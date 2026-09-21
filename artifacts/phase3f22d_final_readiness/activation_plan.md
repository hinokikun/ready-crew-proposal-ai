# Phase3F-22D activation plan

## Decision state

The four runtime roles have source Human Visual PASS and runtime Human Visual PASS. Their templates, semantic bindings, adapter, dispatcher, provenance gate, completeness gate, sample-leak guard, and text-fit guard are ready. `PPTX_APPROVED_NATIVE_RENDERER_ENABLED` remains OFF.

Activation is therefore ready for a separately authorized decision, but is not enabled by this checkpoint.

## Runtime behavior

- With the flag OFF, the existing renderer remains the only production path.
- With the flag ON, Native rendering is attempted only after Human approval, template availability, role-contract validity, adapter success, provenance validation, completeness validation, sample-leak validation, and text-fit validation all pass.
- Current production-like data for these evidence-sensitive roles remains fail-closed and uses the existing renderer. No sample or canonical business values are used as a substitute.
- Verified, provenance-bearing fixture data renders natively for `COMPETITION`, `WIN_PROBABILITY`, `SCHEDULE`, and `ROADMAP`.
- A Native exception falls back for that role and does not remove the slide or abort the deck solely because the optional renderer failed.

## Activation validation order

1. Confirm explicit authorization and keep the source default OFF.
2. Confirm registry approval and frozen template hashes.
3. Run the focused regression recorded in `focused_regression.json`.
4. Run a local or controlled environment Summary/Detail smoke with the flag explicitly ON.
5. Verify current-data fallback and verified-fixture Native paths separately.
6. Perform one Human runtime spot-check per newly activated role.
7. Only then consider an environment-level enablement decision.

No API, Frontend, PDF, DB, auth, or request-schema change is part of this plan.
