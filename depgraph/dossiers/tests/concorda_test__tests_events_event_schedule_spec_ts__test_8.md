---
node_id: concorda-test::tests/events/event-schedule.spec.ts::test@8
node_kind: test
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0aee96878d77186408e42d69825bc17356fe218f668afdd76c493c2f71edd03a
status: current
---

# schedule page loads

## Purpose

Verifies that a "fresh" sailing event (one created without pre-existing logistics or crew) automatically enters an edit mode for the boat owner. This ensures that the owner is immediately prompted to configure the event details rather than being stuck in a read-only view. This test is distinct from general schedule loading tests as it specifically validates the transition from view-mode to edit-mode based on the event's initial state.

## Invariants

- **Requires a "fresh" event state.** The event must be created with no pre-existing logistics or crew to trigger the auto-edit behavior.
- **Uses `ApiClient` for setup.** The test relies on `api.createSailingEvent` and `api.getMyCrewData` to establish the necessary state before navigating to the event detail page.
- **Edit-mode signal is the "Cancel" button.** A successful auto-edit is verified by the presence of the `Cancel` and `Save` buttons.
- **Future-dated events.** Uses a `futureDate` helper to ensure the event is well clear of any seeded/static test fixtures.

## Gotchas

- **Auto-edit-crew was intentionally removed.** Per commit `19c9103`, the system no longer auto-edits the crew section to avoid surprising owners on events that are already set up; this test specifically targets the *logistics* auto-edit for fresh events.
- **Regression on auto-edit trigger.** Previously, the auto-edit was gated purely on `hasPlan`. This caused a bug where regatta events with pre-filled logistics rendered the crew section read-only, preventing owners from assigning crew without manual intervention.
- **Edit-mode disambiguation.** The test uses the presence of the `Cancel` button (`page.getByRole('button', { name: /^cancel$/i })`) as the definitive signal for edit mode, as "Edit" buttons are still visible in view mode.

## Cross-cutting concerns

- **Auth**: Uses `api.login` with `USERS.bob.email` to establish owner identity.
- **Side effects**: Validates the auto-edit behavior which affects the user experience for event owners during the initial setup phase of a regatta.

## External consumers

None known.
