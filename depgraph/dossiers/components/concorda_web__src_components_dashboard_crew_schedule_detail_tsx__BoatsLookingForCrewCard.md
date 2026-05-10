---
node_id: concorda-web::src/components/dashboard/crew-schedule-detail.tsx::BoatsLookingForCrewCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8a0c8fc6ad1ca3b6240c10514d6dc591544f99e9f78d78666927b2fb60b6a165
status: llm_drafted
---

# BoatsLookingForCrewCard

## Purpose

Displays a list of boats within a specific regatta that are actively accepting crew requests. It provides a "request to crew" action for users, allowing them to signal interest in joining a boat. This is distinct from the `AvailableSection` (see sibling dossier), which focuses on individual crew availability; this component is specifically for the "looking for a ride" flow within a race context.

## Invariants

- **`regattaId` is required for data fetching.** If `regattaId` is null, the component renders a fallback message stating the event is not a race.
- **`eventId` is required for the mutation.** The `requestToCrew` call requires the `eventId` to correctly route the request to the specific event context.
- **`requestToCrew` is an async operation.** It manages local state for `requestStatuses` to prevent multiple simultaneous clicks and provides feedback via `toast`.
- **The component handles "already requested" states gracefully.** If the API returns an error indicating a request already exists, the UI updates the status to `requested` rather than showing a destructive error.

## Gotchas

- **`regattaId` vs `eventId` distinction.** While `regattaId` drives the initial fetch of the boat list, the `eventsApi.requestToCrew` call uses the `eventId`. Mixing these up will result in requests being sent to the wrong context.
- **Error handling for existing requests.** Per the logic in `requestToCrew`, an error containing the string `"already"` is treated as a successful state transition (setting status to `requested`) rather than a failure, to prevent user frustration if a request was sent in a previous session.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to call `eventsApi.requestToCrew`.
- **Side effects**: The "bookmark-as-crew" badge (per commit `03d901b`) is part of the broader "looking for a ride" feature set that tracks these interactions.

## External consumers

None known.
