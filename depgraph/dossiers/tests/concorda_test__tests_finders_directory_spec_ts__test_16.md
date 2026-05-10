---
node_id: concorda-test::tests/finders/directory.spec.ts::test@16
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0e94216352ee33ac79367d8dbba2ff45b7eecf12439f482b4bcfd39b0edd4039
status: llm_drafted
---

# shows opted-in members

## Purpose

Verifies the visibility and filtering logic of the Member Directory page. It ensures that members who have opted into the directory are discoverable via search and alphabetical filtering, and that the view toggle (Grid vs. List) functions without breaking the UI state.

## Invariants

- **URL Requirement**: The page must resolve to a path matching `/\/members\/directory/`.
- **Opt-in Visibility**: Only members with the opt-in flag set are expected to appear in the search results (e.g., Alice, Bob, Carol, Eve).
- **View State**: The toggle between 'grid' and 'list' must be functional and not trigger errors during the transition.

## Gotchas

- **Manual Wait Times**: The test relies on `await page.waitForTimeout(1000)` or `500` after search and toggle actions. This suggests the UI or the underlying API response has a non-trivial latency that Playwright's standard auto-waiting isn't catching, or the component state updates are asynchronous.

## Cross-cutting concerns

- **Auth**: Implicitly requires a session/auth state established in `beforeEach` via `DirectoryPage.goto()`.
- **Side effects**: Changes to the directory search or view toggle affect the visibility of the member list component.

## External consumers

None known.
