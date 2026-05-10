---
node_id: concorda-test::tests/events/event-schedule.spec.ts::test@17
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 608ab29beeaa43078a46bd6b67389d95b0acb62b3ebe6767d01c0baaee78f06d
status: current
---

# my schedule tab on dashboard shows events

## Purpose

Verifies that a "fresh" event (one created without a pre-existing plan or crew) automatically enters "edit mode" upon being opened via the members' schedule view. This ensures that boat owners can immediately begin configuring an event without having to manually trigger the edit state first.

## Invariants

- **Requires a fresh event**: The test creates an event via `api.createSailingEvent` with no initial logistics or crew to trigger the auto-edit logic.
- **Auth state is injected via localStorage**: The test manually sets `auth_token` in the browser's `localStorage` to simulate a logged-in session.
- **Navigation path**: The test navigates to `/members?tab=schedule&event=${event.id}` to trigger the specific view-to-edit transition.
- **Edit mode signal**: Success is defined by the presence of the `Cancel` and `Save` buttons, which are only visible when an editor is active.

## Gotchas

- **Auto-edit logic is no longer universal**: Per commit `19c9103`, `auto-edit-crew` was removed to prevent surprising owners on events that are already set up. This test specifically targets the "fresh event" case where the logic still applies.
- **Regression on logistics-only auto-edit**: A previous bug (noted in the source comments) caused the view to remain read-only if logistics were already populated. This test ensures that for a truly fresh event, the user is not blocked from editing.
- **Selector sensitivity**: The test relies on the `Cancel` button (regex `/^cancel$/i`) as the primary disambiguator for edit mode, as it is never present in standard view mode.

## Cross-cutting concerns

- **Auth**: Uses `api.login` and `api.setToken` to establish the session for the `bob` user before injecting the token into the browser.
- **Side effects**: Verifies the behavior of the `members/schedule` route and the `event` detail view transition.

## External consumers

None known.
