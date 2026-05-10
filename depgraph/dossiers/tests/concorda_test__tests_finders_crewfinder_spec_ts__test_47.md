---
node_id: concorda-test::tests/finders/crewfinder.spec.ts::test@47
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ebdbf3dd5b0dea347875eb5e4618b42e535045997f0ef9fabc6e00b9ff5f21f6
status: current
---

# can navigate to crew member profile from finder

## Purpose

Verifies the navigation flow from the Crew Finder view to a specific crew member's profile. It ensures that the UI correctly renders crew cards with functional links and that clicking a member's link successfully transitions the application state to the member detail route.

## Invariants

- **Navigation target** — The destination URL must match the pattern `/\/members\/crewfinder\/crew\//`.
- **Conditional execution** — The test uses a conditional `test.skip` if no crew members are detected in the current seed, preventing false negatives in empty environments.
- **Selector dependency** — Relies on an `<a>` tag with a partial href match for `/members/crewfinder/crew/`.

## Gotchas

- **UI Drift** — The old "Go to Profile" CTA used in empty states has been removed in favor of direct crew cards.
- **Selector Fragility** — Per commit `5836d6a`, the test was recently updated to account for a new profile layout and changed selectors to prevent breakage during the transition to the new profile UI.
- **Seed Dependency** — If the test environment does not include seeded crew members, the test will skip via the `!hasCrew` check.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to access the `/members/` route (inherited from the `crewfinder.spec.ts` suite setup).
- **Side effects**: Changes to the crew card layout or the member detail routing structure will break this test.

## External consumers

None known.
