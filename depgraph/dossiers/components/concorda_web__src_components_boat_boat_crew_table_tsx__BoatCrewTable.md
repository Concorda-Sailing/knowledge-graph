---
node_id: concorda-web::src/components/boat/boat-crew-table.tsx::BoatCrewTable
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fbf1879d83fd9bab29bfa51532560c745cc83f67a0be7347e478aaf5e1dddcbf
status: current
---

# BoatCrewTable

## Purpose

Displays a categorized list of boat crew members, partitioned by status (active, invited, or prospective). It provides administrative controls for boat owners to manage the roster, including removing members, updating roles, and resending invitations. This component is the primary interface for managing the human element of a boat's composition within the dashboard.

## Invariants

- **`isOwner` determines UI visibility.** The administrative columns (e.g., the action column for removing/updating) are only rendered if `isOwner` is true.
- **`onRefresh` is the mandatory callback for mutations.** Any successful call to `boatApi.removeCrew`, `boatApi.resendInvite`, or `boatApi.updateCrew` must trigger `onRefresh` to ensure the parent view reflects the updated state.
- **Status-based filtering is internal.** The component calculates `activeCrew`, `prospectiveCrew`, and `invitedCrew` locally from the `crew` prop to drive the segmented sections.
- **`boatId` is required for all API calls.** Every mutation (remove, resend, update) is scoped to the specific `boatId` provided in props.

## Gotchas

- **`resending` state is per-member.** The `setResending(member.id)` pattern ensures that if a user clicks "resend" on one member, the loading state is tracked specifically for that ID, preventing global UI lockup during network latency.
- **Error handling uses `toast` with variant fallback.** Per the implementation of `handleRemove` and `handleRoleChange`, errors are caught and passed to a `toast` component; if the error is not a standard `Error` object, it defaults to a generic "Failed to..." message to prevent UI crashes.

## Cross-cutting concerns

- **Auth**: Requires authenticated user with owner permissions to successfully execute `boatApi` mutations.
- **Side effects**: Successful mutations trigger `onRefresh`, which typically causes a re-fetch of the boat data in the parent `BoatOwnerView` or `BoatProfileTab`.

## External consumers

None known.

## Open questions

- The `handleRoleChange` function currently accepts a raw `string` for the role; should this be constrained by a specific `Role` union type to prevent invalid API payloads?
