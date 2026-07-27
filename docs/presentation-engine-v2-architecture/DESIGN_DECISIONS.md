# Design Decisions

## Why Deck Planner Comes First

The deck must define the order of persuasion before any slide-level content is written. Without deck structure, later modules would optimize individual pages without a coherent proposal story.

## Why Evidence Is Separate

Evidence separation prevents Message Designer from inventing unsupported claims. It also lets the system carry missing evidence forward as an explicit customer-facing risk.

## Why Message Designer Is Independent

Message should be written before layout so the core point is not distorted by a template. This supports one-slide-one-message discipline.

## Why Slide Intent Exists

Message Designer says what to say. Slide Intent says what the viewer should see. This layer prevents Visual Director from reinterpreting the proposal strategy.

## Why Renderer Is Last and Dumb

Renderer should be deterministic and boring. It should draw shapes from blueprint data, not decide business meaning.

## Why Alpha Integration Is Offline

Alpha Integration finds contract mismatch and story/evidence/message drift before runtime integration. It reduces risk without changing production behavior.
