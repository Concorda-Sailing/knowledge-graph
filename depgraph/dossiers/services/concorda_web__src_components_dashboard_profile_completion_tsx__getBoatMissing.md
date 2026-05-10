---
node_id: concorda-web::src/components/dashboard/profile-completion.tsx::getBoatMissing
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae66ff79a68a2b3dc7bbac90f3e04d49409a299eca7ca97dc51f9df90252a2ac
status: llm_drafted
---

# getBoatMissing

## Purpose

Identifies missing required fields in a user's boat profile to drive the "Profile Completion" UI. It checks for the presence of `sail_number`, `name`, and `manufacturer` on the first boat in the provided array. It is distinct from `getAvailabilityMissing` (the sibling function above it), which focuses on temporal availability rather than physical boat attributes.

## Invariants

- **Input is an array of `Boat` objects.** The function expects a list of boats, but logic is strictly tied to the first element (`boats[0]`).
- **Returns a list of strings.** If all required fields are present, it returns an empty array `[]`.
- **Requires three specific fields for "completion".** A boat is only considered "complete" if `sail_number`, `name`, and `manufacturer` are all truthy.

## Gotchas

- **Strictly checks only the first boat.** If a user has multiple boats, this function only validates the first one in the array. If the first boat is incomplete but the second is complete, it will still return a list of missing fields.
- **Implicit truthiness check.** Because it uses `b.sail_number && b.name && b.manufacturer`, a value of `0` or an empty string `""` for a sail number will trigger a "missing" status.

## Cross-cutting concerns

- **Auth**: none.
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Drives the "Profile Completion" progress indicators in the dashboard.

## External consumers

None known.
