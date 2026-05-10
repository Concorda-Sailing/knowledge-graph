---
node_id: concorda-web::src/components/boat/boat-page.tsx::BoatPage
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 582fa006cd9270cd95361b59e17da3b901f3ce646a1ae8800e127ceedda7c421
status: current
---

# BoatPage

## Purpose

The `BoatPage` component acts as a role-based router for boat-specific detail views. It resolves the viewer's identity by checking the `boatApi.getCrew(boatId)` endpoint to determine if the current user is an "owner" or an "active crew" member. This ensures that `BoatOwnerView` and `BoatCrewView` are only rendered when the user has the appropriate permissions and status.

## Invariants

- **Requires a valid `boatId`** to perform the resolution.
- **Resolution is identity-dependent.** The component must check both the presence of the user in the crew list and their `status === "active"` to grant access.
- **Returns a `no-access` state** if the user is not found in the crew list or if their status is not "active".
- **Uses `useWsFreshness`** to trigger a re-resolution whenever the crew list changes.

## Gotchas

- **Role-based splitting is a recent change.** Per commit `4fad70e`, this component was recently refactored to split the view between `BoatOwnerView` and `BoatCrewView` based on the user's role. Ensure any logic regarding "who sees what" is updated in both sub-views to maintain consistency with this split.

## Cross-cutting concerns

- **Auth**: Depends on `useAuth()` to provide the current `user.id`.
- **Websocket**: Listens to the `boat_crew.updated` event via `useWsFreshness` to trigger a re-resolve of the view.
- **Side effects**: Re-resolves the view when the crew list changes, ensuring the UI reflects real-time status changes (e.g., a user being promoted or removed from the crew).

## External consumers

None known.
