---
node_id: concorda-web::src/app/members/admin/events/series/page.tsx::SeriesDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: dccafd1e31523af0c188722adc3b40fe7db43e8de260a33e0f375e8f4292475e
status: current
---

# SeriesDialog

## Purpose

The `SeriesDialog` component provides a modal interface for creating or editing a racing series. It manages a local form state that transforms between the raw `SeriesDetail` API shape (which uses UTC ISO strings and arrays) and the human-readable input format (which uses local date strings and comma-separated strings) required for the UI.

## Invariants

- **Timezone conversion is mandatory.** The component uses `utcIsoToOrgDateInput` and `orgDateInputToUtcIso` with the organization's timezone to ensure date inputs in the form match the intended UTC representation in the database.
- **Input/Output mismatch handling.** The `scoring_system` and `qualifier` fields are stored as arrays in the API but are managed as comma-separated strings within the form state.
- **Required fields.** The `name` field is a hard requirement for submission; the `handleSave` function returns early if `form.name` is empty.
- **State reset on open.** The `useEffect` hook resets the form state whenever the `series` object or the `open` visibility state changes, ensuring a clean slate for new entries.

## Gotchas

- **Mobile layout constraints.** Per commit `0564f06`, the dialog is styled with `max-w-[calc(100vw-2rem)]` and a `max-md:w-full` button to prevent the dialog from overflowing the viewport or breaking the footer layout on small screens.
- **Manual parsing of arrays.** The `scoring_system` and `qualifier` fields are converted via `.split(",").map((s) => s.trim()).filter(Boolean)`. If a user enters trailing commas or extra spaces, the filter ensures the API receives clean data.
- **Type coercion.** The `num_races` field is handled as a string in the local form state but must be cast via `parseInt` before being sent to the `seriesApi`.

## Cross-cutting concerns

- **Auth**: Requires authenticated admin access to call `seriesApi.update` or `seriesApi.create`.
- **Side effects**: Successful submission triggers the `onSuccess` callback, which typically refreshes the `SeriesPage` list view.

## External consumers

None known.
