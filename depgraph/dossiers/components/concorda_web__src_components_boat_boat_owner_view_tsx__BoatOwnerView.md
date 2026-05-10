---
node_id: concorda-web::src/components/boat/boat-owner-view.tsx::BoatOwnerView
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3c982821af582f59eb183eb742d455d1d55fcb9823fe34be9eb3cb8926e685e1
status: current
---

# BoatOwnerView

## Purpose

The central management view for a boat's ownership and identity. It provides the interface for owners to manage the boat's profile, including the banner image, the boat's "resume" (biographical data), and the list of crew members. It acts as the orchestrator for sub-components like `BoatResumeView`, `OwnersSection`, and `PendingApprovalsPanel`.

## Invariants

- **Requires `boatId`** — The component relies on a valid string ID to fetch the specific boat entity from the `profileApi`.
- **Ownership check is strict** — A user is only considered an owner if they have a `role === "owner"` AND a `status === "active"` within the `crew` array.
- **State-driven UI** — The view manages multiple local states for loading, error handling, and UI modes (e.g., `editingResume`, `bannerCropOpen`) to ensure a smooth transition between viewing and editing.
- **Banner interaction** — The banner click handler handles touch device logic specifically to prevent accidental triggers on mobile.

## Gotchas

- **Co-owner invitation logic** — Per commit `47688ac`, users must have an existing "Boat Owner" membership to accept a co-owner invite. This is a critical permission check that prevents unauthorized elevation of status.
- **Mobile/Touch interaction** — The `handleBannerClick` function includes a specific `setTimeout` (4000ms) to manage `mobileActive` state. This prevents the file input from being triggered repeatedly on touch devices during a single tap.
- **Form-ref dependency** — The `handleResumeSave` function relies on `resumeFormRef.current.save()`. If the ref is not properly attached or the component is unmounted, the save operation will fail silently or throw, as seen in the `try/catch` block.

## Cross-cutting concerns

- **Auth**: Uses `useAuth()` to identify the current user for the `isOwner` check.
- **Side effects**: Updating the boat via `profileApi` or the `resumeForm` requires a call to `refresh()` from `useBoats` to ensure the sidebar and other boat-level data stay in sync.

## External consumers

None known.
