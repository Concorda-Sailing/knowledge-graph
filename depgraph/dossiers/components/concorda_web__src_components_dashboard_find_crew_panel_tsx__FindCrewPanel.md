---
node_id: concorda-web::src/components/dashboard/find-crew-panel.tsx::FindCrewPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b47f631b986c991232b0043af2d1245f84aa756e1dc9ac454739a817e702c5a2
status: current
---

# FindCrewPanel

## Purpose

The `FindCrewPanel` is a side-sheet UI component used to discover and invite sailors to a specific regatta. It fetches a list of potential crew members via `regattaApi.getMatchRoster` and filters out individuals who are already in the pool or otherwise excluded. It is distinct from the `AvailableSection` in that it is a high-intent "discovery" tool (a Sheet) rather than a passive display of existing crew.

## Invariants

- **`regattaId` is required.** The component relies on this ID to fetch the correct roster via `regapi.getMatchRoster`.
- **`excludePersonIds` must be a list of IDs to hide.** This includes people already in the crew or those explicitly blocked.
- **`onInvite` is an async function.** It must accept a `personUuid` and return a `Promise<void>` to allow the component to manage the `invitingId` loading state.
- **`open` state controls the fetch.** The `useEffect` hook only triggers the API call when `open` transitions to `true`, preventing unnecessary network calls while the sheet is closed.

## Gotchas

- **Extraction Refactor:** Per commit `f13ba7c`, this component was recently extracted from `event-crew-card`. Ensure that any logic previously handled by the parent card is now correctly passed in via props (like `excludePersonIds` or `alreadyInPool`) rather than assuming local state availability.
- **Error Handling:** The component uses `useToast` to surface errors. If `onInvite` fails, the error message is caught and displayed as a `destructive` toast; ensure any new error types are compatible with the `err instanceof Error` check in the `invite` function.

## Cross-cutting concerns

- **Auth**: Relies on `regattaApi` which requires an authenticated session (bearer token).
- **Side effects**: Successful completion of `onInvite` triggers a toast notification, signaling to the user that they should now look for the "Notify" action elsewhere in the UI.

## External consumers

None known.
