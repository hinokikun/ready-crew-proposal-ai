# Integration Plan

Version49 is not connected to production. A future integration should follow this order:

1. Keep the generator offline and behind an explicit feature flag.
2. Add Human Review UI only after the Sales Assistant Brief contract is approved.
3. Store only approved, minimal sales-assistant metadata if DB persistence is required.
4. Never log customer full text, API keys, tokens, or passwords.
5. Keep Strategy Brief as the source of strategy decisions.

No frontend, API, DB, migration, PPTX, Beautiful.ai, or proposal generation integration is included in Version49.

