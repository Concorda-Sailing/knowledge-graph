---
node_id: concorda-web::src/components/boat/owners-section.tsx::InviteCoownerDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5ff0176cd8a0a95f1d2b9620c9c35ac2841c64aa2ceda6dc7528efe3a78d8d01
status: llm_drafted
---

# InviteCoownerDialog

## Purpose

The `InviteCoownerDialog` provides a UI for adding new members to a boat via a directory search. It manages a debounced search against the person directory and handles the invitation lifecycle, including loading states and error handling. Use this component when a user needs to invite a person by name/email rather than selecting from a pre-existing list of roles.

## Invariants

- **Search threshold:** The directory search only triggers when `search.trim().length >= 2`.
- **Abortable requests:** Uses `AbortController` to cancel in-flight directory fetches if the user continues typing or closes the dialog.
- **Identity requirement:** The `selected` person must be non-null for `sendInvite` to proceed.
- **API Contract:** Calls `boatApi.coownerInvite(boatUuid, { person_uuid: string })`.

## Gotchas

- **Directory-first UX:** Per commit `eb382d2`, this is a "directory-only invite dialog." It is designed to search the directory first, rather than relying on a static list of roles.
- **Membership requirement:** Per commit `47688ac`, the backend requires the inviter to have a Boat Owner membership to successfully execute the invite; failure to meet this results in an error caught in the `try/catch` block.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` for the directory search.
- **Side effects**: On `onSuccess`, the parent component (typically `BoatOwnerView`) must refresh its list of owners to reflect the new co-owner.

## External consumers

None known.
