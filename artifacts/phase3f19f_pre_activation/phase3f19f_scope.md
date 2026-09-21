# Phase3F-19F Pre-Activation Scope

This is a change plan only. No activation is performed by Phase3F-19F-PRE.

If the runtime `PROPOSAL_SUMMARY` output receives an explicit Human Visual PASS, Phase3F-19F will:

1. Reconcile the approval state through the existing authoritative native registry only.
2. Enable `PPTX_APPROVED_NATIVE_RENDERER_ENABLED` through the selected server-side environment, with the source default remaining OFF.
3. Run the minimal post-activation validation defined in `post_activation_validation_plan.md`.
4. Confirm that every ineligible or evidence-blocked role continues through the existing renderer.
5. Keep the existing adapter, provenance, sample-leak, text-fit, Quality Gate, auth, history, PDF, and API paths unchanged.

Phase3F-19F will not redesign templates, rewrite the data model, add request fields, mutate frozen PPTX sources, add continuation slides to Summary, or alter Summary/Detail role selection.

Current decision: **NO-GO** because runtime `PROPOSAL_SUMMARY` Human Visual Review is still pending. The feature flag remains OFF.
