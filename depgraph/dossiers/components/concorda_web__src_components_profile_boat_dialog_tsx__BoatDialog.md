---
node_id: concorda-web::src/components/profile/boat-dialog.tsx::BoatDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: cb04bbcfc02033802e347080602c7bde22aee9355ac0ab20baee6f48636bba3b
status: current
---

# BoatDialog

## Purpose

A modal dialog used for both creating a new boat entry and editing an existing one. It manages a local form state that synchronizes with the `boat` prop when the dialog opens. Use this component when a user needs to update their vessel details or upload a profile picture within the profile section.

## Invariants

- **`boat` prop determines mode.** If `boat` is truthy, the dialog operates in "Edit Mode"; if `null`, it operates in "Create Mode".
- **Form reset on open.** The `useEffect` hook resets `formData` and `currentPictureUrl` whenever the `open` state or `boat` object changes to ensure stale data from a previous session doesn't persist.
- **Numeric conversion.** `length` and `draft` are stored as strings in the local `formData` state but are derived from `boat.length?.toString()` to ensure compatibility with the input fields.
- **Picture upload is a side effect.** Calling `handlePictureUpload` calls `profileApi.uploadBoatPicture` and updates the local `currentPictureUrl` upon success.

## Gotchas

- **`boat` must be provided for updates.** The `handlePictureUpload` function returns early if `!boat`, meaning you cannot upload a picture during the initial "Create" phase of a boat; the boat must exist in the database first.
- **Manual state sync required.** Because the component manages its own `formData` state, any changes made to the `boat` object externally will not be reflected in the dialog unless the `open` prop is toggled or the component is re-mounted.

## Cross-cutting concerns

- **Auth**: Uses `profileApi` which requires an authenticated session.
- **Side effects**: Successful form submission or picture upload should trigger a refresh of the `BoatsList` component to ensure the UI reflects the updated boat data.

## External consumers

- `BoatsList` (likely the primary caller for both creation and editing flows).

## Open questions

- Should the picture upload be decoupled from the boat creation flow to allow users to upload an image during the initial "Create" step? Currently, the `!boat` guard prevents this.
