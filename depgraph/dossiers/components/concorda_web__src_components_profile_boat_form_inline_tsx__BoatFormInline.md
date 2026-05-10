---
node_id: concorda-web::src/components/profile/boat-form-inline.tsx::BoatFormInline
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 1c6368ef98808c2e40ee30a16f300fd99f376ae6ae1d3b8ccf3e1274b30e7c9a
status: current
---

# BoatFormInline

## Purpose

Provides an inline form for creating or editing a boat's details. It handles both the creation of a new boat and the updating of an existing one, managing local state for form fields like sail number, manufacturer, and location. Use this component when a user needs to modify their boat profile without navigating away from the current view.

## Invariants

- **`boat` prop determines mode**: If `boat` is null, the form operates in "create" mode; if `boat` is provided, it operates in "edit" mode.
- **`onSuccess` and `onCancel` are mandatory**: The component relies on these callbacks to signal the end of the form lifecycle to the parent.
- **`isEdit` check is critical for co-owner logic**: The `coownerTarget` logic only executes if `isEdit` is false (creation mode), as per the implementation in `handleSave`.
- **Numeric conversion**: `formData.length` and `formData.draft` are stored as strings in state but must be parsed/validated as numbers during the save process.

## Gotchas

- **Co-owner request path**: Per commit `60821ed`, the form includes a specific path for requesting a co-owner during the "add-boat" flow. This is a distinct logic branch from the standard `updateBoat` call.
- **Alignment requirement**: Per commit `fbb71f5`, back buttons must remain left-aligned to maintain the inline panel pattern used throughout the profile section.
- **Manual numeric validation**: The `handleSave` function performs a manual check on `formData.length` to ensure it is a positive number before calling the API.

## Cross-cutting concerns

- **Auth**: Uses `profileApi` and `boatApi` which require a valid session/bearer token.
- **Side effects**: Successful updates/creations trigger `onSuccess`, which typically refreshes the `BoatsList` or the user's profile view.

## External consumers

None known.
