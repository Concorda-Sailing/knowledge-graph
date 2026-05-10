---
node_id: concorda-web::src/components/admin/organizing-authorities-selector.tsx::OrganizingAuthoritiesSelector
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a23b672639ab2c975d4d523cc10c0d07ca114d21a312c89b0ad113efd9405bfa
status: current
---

# OrganizingAuthoritiesSelector

## Purpose

A multi-select input component used for assigning one or more organizations (Organizing Authorities) to a specific entity (like a race or event). It provides a searchable dropdown to add organization IDs and a badge-based interface to remove them. Use this when an admin needs to associate multiple organizational entities with a single record.

## Invariants

- **`value` is an array of strings.** The component expects an array of organization IDs.
- **`onChange` returns the full updated array.** Adding or removing an organization triggers a full replacement of the current `value` list.
- **`organizationsApi.list()` is the source of truth.** The component fetches the full list of available organizations on mount to populate the search and display logic.
- **Input is case-insensitive.** The search filter uses `.toLowerCase()` on both the input and the organization name.

## Gotchas

- **Search results are limited to 8 items.** The `suggestions` logic uses `.slice(0, 8)` to prevent long dropdown lists from obscating the UI, which might make it feel like some organizations are "missing" if the user doesn't type a specific enough string.
- **Click-away behavior relies on `mousedown`.** The component uses a `mousedown` listener on the `document` to close the suggestion list when clicking outside the `wrapperRef`. If a developer changes this to `click`, it may cause a race condition with the input focus.

## Cross-cutting concerns

- **Auth**: Depends on `organizationsApi.list()` which requires a valid session/token (standard `ApiClient` behavior).
- **Side effects**: Used in admin forms to set the organizational responsibility for events or races.

## External consumers

None known.
