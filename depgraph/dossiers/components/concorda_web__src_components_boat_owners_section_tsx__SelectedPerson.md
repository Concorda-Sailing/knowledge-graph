---
node_id: concorda-web::src/components/boat/owners-section.tsx::SelectedPerson
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 602c4994354e5771fd3fdbdf9582c39e598d0104dbd223966839a9e596a6e7eb
status: llm_drafted
---

# SelectedPerson

## Purpose

Displays the identity of a currently selected person (likely a boat owner or co-owner) within the owners settings section. It provides a visual summary using an avatar with initials and the person's name/email, alongside a "Change" button to trigger a selection reset. This is a sub-component of the boat owners management flow.

## Invariants

- **Input must be a `DirectoryPerson` object.** The component expects `first_name`, `last_name`, and optionally `email` and `picture_url`.
- **Initials generation is fallback-safe.** If `first_name` or `last_name` are missing, it defaults to an empty string to prevent `undefined` appearing in the `AvatarFallback`.
- **`onClear` is a required prop.** The "Change" button relies on this callback to allow the user to exit the current selection state.

## Gotchas

- **UI layout constraints.** Per commit `3402684`, owner-only strips (where this component likely resides) must handle stack actions and layout carefully to avoid full-width issues on `<md` screens.
- **Identity context.** Recent changes in the `coowner` feature set (commits `47688ac` and `eb382d2`) suggest that the person displayed here is subject to stricter membership requirements (e.g., requiring Boat Owner membership to accept invites).

## Cross-cutting concerns

- **Auth**: The visibility and interaction of this component are tied to the user's ability to manage boat ownership/co-ownership.
- **Side effects**: Changing the person via `onClear` triggers a state change in the parent `owners-section.tsx`, which may affect the visibility of invite/upgrade prompts.

## External consumers

None known.
