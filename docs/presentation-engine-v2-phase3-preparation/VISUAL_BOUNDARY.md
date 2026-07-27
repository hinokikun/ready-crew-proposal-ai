# Visual Boundary

## Main Boundary

Visual Plan Contract decides how a slide should be visually represented, but it
does not render the slide.

## Allowed

- visual strategy
- layout strategy
- emphasis strategy
- information priority
- component candidates
- diagram strategy
- chart strategy
- image strategy
- table strategy
- callout strategy
- icon strategy
- risk flags
- confidence

## Prohibited

- PowerPoint generation
- slide coordinates
- shape IDs
- actual diagram objects
- actual chart objects
- theme generation
- font sizes
- color palette generation
- external image fetching
- API calls
- database writes
- frontend state

## Responsibility Split

| Module | Responsibility |
|---|---|
| Slide Intent | defines abstract visual intent |
| Visual Plan Contract | defines concrete-but-renderer-agnostic visual plan |
| Visual Director | future engine that creates Visual Plan Contract |
| Blueprint Composer | future module that converts Visual Plan to renderable blueprint |
| Renderer | future module that draws PowerPoint objects |

## Blocker Rule

If Visual Plan requires evidence that does not exist, the plan must expose a risk
flag instead of inventing evidence or generating a fake chart.
