---
node_id: concorda-web::src/app/members/boatfinder/apply-dialog.tsx::ApplyDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ac11a65611652975c0dc31cf448a6c114f0b26e23e36e6d68893782aa66e04d0
status: current
---

# ApplyDialog

## Purpose

The `ApplyDialog` handles the user interface for expressing interest in a boat, either as a general application or a specific race crew request. It differentiates between a generic "interest" message and a "race request" based on the presence of an `eventId`. This allows the same UI component to serve both the general Boat Finder discovery flow and the specific race-day scheduling flow.

## Invariants

- **Message length is capped at 2000 characters** via the `maxLength` prop on the `Textarea`.
- **`eventId` presence determines the API endpoint**: if `eventId` is truthy, it calls `eventsApi.requestToCrew`; otherwise, it calls `boatfinderApi.apply`.
- **The dialog auto-closes 1.5s after a successful submission** via `setTimeout(() => onOpenChange(false), 1500)`.
- **The first name is extracted for the greeting** using `ownerName.split(" ")[0]`.

## Gotchas

- **`requestToCrew` requires the boat UUID** — Per commit `f876f14`, the `boat_uuid` must be passed through the `requestToCrew` call to ensure the backend correctly links the crew request to the specific boat instance during a race.
- **Error handling for duplicate requests** — The component explicitly checks if an error message includes the string `"already"` (case-insensitive) to provide a specific "Already requested" toast instead of a generic error. This is a hard-coded check against the current `eventsApi` error response pattern.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Successful submission triggers a toast notification that informs the user that the owner will be notified.

## External consumers

None known.
