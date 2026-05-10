---
node_id: concorda-web::src/components/boat/boat-crew-invite.tsx::BoatCrewInvite
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c3878976076ba995b8d9a78b13a258215feb16ab72c87234dda9374fdce4dae4
status: llm_drafted
---

# BoatCrewInvite

## Purpose

A modal dialog for managing boat crew invitations via three distinct methods: searching for existing people, entering email addresses, or generating a shareable link/QR code. It serves as the primary interface for expanding a boat's membership. Use this component when a user needs to add new members to a boat, rather than using the general profile management tools.

## Invariants

- **`boatId` is required** to scope all API calls (`createShareInvite`, `getShareInviteStatus`).
- **`onSuccess` is called** when a share token is consumed, allowing the parent component to refresh its state.
- **`shareToken` is transient.** The component manages its own lifecycle for the token to ensure the QR code stays fresh.
- **`defaultMembershipSlug` is required** for the `signupUrl` to be a valid, functional link.

## Gotchas

- **Token Refresh Polling:** The component implements a polling interval (`setInterval`) that monitors `getShareInviteStatus`. When a status changes to `"consumed"`, it immediately nullifies the `shareToken` and triggers `onSuccess`. This ensures that if a user scans a QR code and joins, the owner's view updates to show a fresh, unused token for the next person without manual intervention.
- **Tab-Switching State:** The `shareToken` is persisted in local state even if the user switches from the "share" tab to "search" and back. This prevents unnecessary API calls to `createShareInvite` unless the component is unmounted or the token is explicitly consumed.
- **URL Construction:** The `signupUrl` relies on `window.location.origin`. In SSR environments or non-browser contexts, this could fail, though the component guards against this with a `typeof window` check.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to call `boatApi.createShareInvite`.
- **Side effects**: Triggers `onSuccess` which typically refreshes the boat's crew list in the parent view.

## External consumers

None known.
