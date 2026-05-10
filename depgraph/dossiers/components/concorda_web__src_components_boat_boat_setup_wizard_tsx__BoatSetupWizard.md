---
node_id: concorda-web::src/components/boat/boat-setup-wizard.tsx::BoatSetupWizard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4fe70273c04210da0d8d9e5786b298e446c7e230c40a2efb75aa5e93083e77ff
status: current
---

# BoatSetupWizard

## Purpose

A multi-step onboarding wizard used to collect and update essential boat metadata (details, resume, positions, and banner image). It is used during the initial user setup flow to ensure a `Boat` object is sufficiently populated before the user enters the main dashboard. Use this component when a user needs to complete their profile or update high-level boat identity details.

## Invariants

- **Requires a `boat` object** with a valid `id` to fetch and update data via `profileApi`.
- **`onComplete` is the terminal callback** triggered after the final step is successfully processed.
- **`onPictureUpload` and `onPictureRemove` are externalized**; the component manages the local UI state for cropping/zooming, but the actual file persistence is handled by the parent.
- **`sail_number` is a required field** for the `handleSaveDetails` step; the save operation will return early if this is empty.
- **Numeric fields (`length`, `draft`) are cast to floats** during the `updateBoat` call to ensure type-safety with the backend.

## Gotchas

- **Mobile layout reflow:** Per commit `920fb28`, the wizard requires a single-column reflow and stacked navigation buttons to prevent layout breakage on small screens.
- **Step-based state management:** The component uses local `useState` for different steps (e.g., `form` for details, `selectedPositions` for positions). If a user navigates away and returns, local state for the current step may be lost unless the parent manages the lifecycle.

## Cross-cutting concerns

- **Auth**: Relies on `profileApi` which requires a valid session/bearer token.
- **Side effects**: Successful completion updates the `Boat` object, which is a dependency for the `BoatHeader` and `BoatProfileTab` components.

## External consumers

None known.
