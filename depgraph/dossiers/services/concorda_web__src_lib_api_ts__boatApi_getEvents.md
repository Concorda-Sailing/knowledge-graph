---
node_id: concorda-web::src/lib/api.ts::boatApi.getEvents
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea27ef65389c4978857a42598f272dc1a5cc68f2445cfb9c212d010b409670de
status: llm_drafted
---

# boatApi.getEvents

## Purpose

Fetches the list of events associated with a specific boat. It is the primary method for retrieving the event timeline for a boat's context, used by both the general boat view and the owner-specific management views.

## Invariants

- **Method is GET** — performs a standard fetch without a body.
- **Requires `boatId`** — the path is constructed using a string-based `boatId`.
- **Returns `BoatEvent[]`** — the response is a typed array of event objects.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to resolve.

## Gotchas

- **Decoupling from `mySchedule`** — per commit `1b5d864`, this endpoint is distinct from the user's personal schedule; it returns the boat's events regardless of the viewer's personal involvement.
- **Avoid `mySchedule` coupling** — do not attempt to filter or join this data with user-specific schedule logic within this call; that logic was explicitly moved/dropped in `1b5d864` to ensure the detail page remains a pure boat-centric view.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated`.
- **Side effects**: Data from this call populates the event list in `BoatInline` and the `BoatOwnerView`.

## External consumers

None known.
