---
node_id: concorda-test::tests/finders/crewfinder.spec.ts::test@14
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: aa48d388540146fdf0cfbdb872949f413e8c3af0c90ee56981dc9cbaab3a10b5
status: current
---

# non-boat-owner sees crew finder (no gate)

## Purpose

Verifies the accessibility and behavior of the Crew Finder view for non-boat-owners. It ensures that the unified finder correctly redirects to the `tab=crew` view and that users can navigate from the crew list to individual member profile pages.

## Invariants

- **Redirect behavior**: Accessing the `/members/crewfinder` path must redirect to `/members/finder?tab=crew`.
- **Tab selection**: The "Crew" tab must be visible and have `aria-selected="true"` when the view loads.
- **Navigation path**: Crew member links must follow the pattern `/members/crewfinder/crew/[id]/`.

## Gotchas

- **UI Drift/Selector Fragility**: Recent changes to the profile layout and the removal of the "Go to Profile" CTA in the empty state have made selectors sensitive. See commit `5836d6a` regarding the new profile layout.
- **Selector Alignment**: The test relies on specific roles (e.g., `page.getByRole('tab', { name: /^crew$/i })`) which were recently updated to align with the actual UI; failing to use the regex name pattern will cause the test to fail. See commit `f552929`.
- **Data Dependency**: The profile navigation test (`test@14`) is susceptible to empty seed data. If no crew members are present in the test database, the test skips via `test.skip(true, 'no crew members in seed')`.

## Cross-cutting concerns

- **Auth**: Implicitly requires an authenticated session (via `CrewfinderPage.goto()`), though this specific test focuses on the "non-owner" view permissions.
- **Side effects**: Changes to the crew card layout or the `/members/crewfinder/crew/` routing pattern will break this test.

## External consumers

None known.
