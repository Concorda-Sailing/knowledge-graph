---
node_id: concorda-web::src/components/profile/preferred-organizations-selector.tsx::PreferredOrganizationsSelector
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 219252310c5c41bed09747a5284d7da05d664d90813dd69aef0c8ed8ca894436
status: llm_drafted
---

# PreferredOrganizationsSelector

## Purpose

A UI component for selecting preferred racing organizations within the user profile. It provides an autocomplete search interface that filters the global list of organizations via `organizationsApi.list()`. It is distinct from a standard multi-select by using a text input to filter results, ensuring users can only select valid, existing organizations.

## Invariants

- **`value` is an array of strings** representing organization IDs.
- **`onChange` returns the full updated array of IDs**, not just the newly added/removed ID.
- **The component fetches its own data** via `organizationsApi.list()` on mount.
- **Input filtering is case-insensitive** and trims whitespace to prevent selection errors.
- **Selection is restricted to the fetched list**; the `suggestions` logic ensures only valid IDs are surfaced to the user.

## Gotchas

- **Click-away behavior relies on a manual `mousedown` listener** on the `document` to close the suggestion dropdown. If the `wrapperRef` is not correctly attached to the container, the dropdown may fail to close when clicking outside.
- **The `label` fallback logic** (`org?.name ?? \`${id.slice(0, 8)}…\``) is a safety measure for when the API returns an ID that isn't in the current local `orgs` state.

## Cross-cutting concerns

- **Auth**: Uses `organizationsApi.list()`, which requires a valid session/bearer token.
- **Side effects**: Updates the user's profile preferences, which may affect visibility or filtering in other parts of the profile view.

## External consumers

None known.
