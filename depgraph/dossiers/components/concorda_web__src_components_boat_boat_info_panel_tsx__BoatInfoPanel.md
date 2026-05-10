---
node_id: concorda-web::src/components/boat/boat-info-panel.tsx::BoatInfoPanel
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a1f0724aeb219ea2d603ea1a9ec8d184544a51d2f167fc7a4ac8358131346e9f
status: llm_drafted
---

# BoatInfoPanel

## Purpose

Provides an editable interface for a boat's metadata, allowing owners to update details like sail number, manufacturer, and physical dimensions. It manages its own local form state to allow users to edit fields without immediate side effects until "Save" is triggered. Use this when a user needs to modify boat-specific attributes (e.g., length, draft, or location) within a profile or dashboard view.

## Invariants

- **Input is a `Boat` object.** The component relies on the `boat.id` to target the correct resource during updates.
- **`onUpdate` is a required callback.** The parent component must provide a function to trigger a re-render or state refresh after a successful `profileApi.updateBoat` call.
- **Numeric conversion is handled locally.** Fields like `length`, `draft`, `hard_cap`, and `soft_cap` are converted from string inputs to `parseFloat` or `parseInt` before being sent to the API.
- **`isOwner` determines visibility/intent.** While the component accepts `isOwner`, the actual permission logic is handled by the parent (see `BoatOwnerView`).

## Gotchas

- **Mobile reflow issues.** Per commit `e4b6616`, this panel requires specific attention to layout when used on mobile devices to ensure the single-column reflow works correctly.
- **Manual type casting.** The `handleSave` function uses a type cast (`as BoatUpdate`) to satisfy the API. If new fields are added to the `Boat` type, they must be explicitly handled in the `form` state and the `handleSave` mapping to avoid being ignored or causing type errors.

## Cross-cutting concerns

- **Auth**: Uses `profileApi.updateBoat`, which requires a valid bearer token (managed by `ApiClient`).
- **Side effects**: Successful updates trigger `onUpdate`, which typically refreshes the `BoatProfileTab` or the `BoatOwnerView` to reflect the new data.

## External consumers

None known.
