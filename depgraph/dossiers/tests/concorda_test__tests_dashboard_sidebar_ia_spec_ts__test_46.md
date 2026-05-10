---
node_id: concorda-test::tests/dashboard/sidebar-ia.spec.ts::test@46
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65fbbfa765a83363bff0fad3eef8fa4968ee9af2ad818a66c678773163001464
status: llm_drafted
---

# /members/crewfinder redirects to /members/finder?tab=crew

## Purpose

Verifies the legacy URL redirect logic for the "Finder" feature. It ensures that users navigating to the deprecated `/members/crewfinder` and `/members/boatfinder` endpoints are correctly redirected to the unified `/members/finder` view with the appropriate `tab` query parameter.

## Invariants

- **Requires authenticated state.** Uses `storageState: 'auth-states/member.json'` to ensure the redirect occurs within a valid session context.
- **Redirect target must include query params.** The target URL must match the regex pattern `/\/members\/finder\?.*tab=(crew|boats)/` to pass.
- **Redirects are path-specific.** `/members/crewfinder` must map to `tab=crew` and `/members/boatfinder` must map to `tab=boats`.

## Gotchas

- **Mobile viewport stability.** Per commit `69f60cc`, assertions on the finder/tablist require waiting for the tablist and checking `aria-selected` to avoid flakiness in mobile viewports.
- **Alignment with UI changes.** Per commit `705f5bd`, this suite must be re-aligned whenever the test host UI structure changes to prevent false negatives in the redirect assertions.

## Cross-cutting concerns

- **Auth**: Uses `auth-states/member.json` via `test.use`.
- **Side effects**: Verifies the navigation flow for the "Finder" component-set.

## External consumers

None known.
