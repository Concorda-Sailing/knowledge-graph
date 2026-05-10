---
node_id: concorda-web::src/components/regatta/regatta-detail-sections.tsx::Cell
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d40b8c30451082b5c2548588a22dd2bba28143e01b703a070c900d77afb4fa33
status: current
---

# Cell

## Purpose

A low-level layout primitive used to display a metadata label alongside its corresponding value. It is used within `RegattaDetailSections` to provide a consistent visual structure for regatta-specific metadata (e.g., "Max Races", "RC Channel"). It is distinct from `LinkSlot` in that it is a purely presentational wrapper for text/data and does not handle URL resolution or authentication-based routing.

## Invariants

- **Label is a string.** The `label` prop is a required string used for the small, muted header text.
- **Children are ReactNode.** The `children` prop accepts any valid React element, including the `<Dash />` component used for empty states.
- **Fixed vertical stack.** The component always renders the label above the content with a specific `mt-0.5` margin on the child container.

## Gotchas

- **Empty states use `<Dash />`.** Per the sibling component `Dash`, if a value is null or undefined, the component should render the `<Dash />` component (which renders a "—" em-dash) rather than an empty string or null to maintain layout stability.
- **Layout dependency.** Because it is used in a `grid-cols-2 md:grid-cols-4` layout in the parent, changing the padding or font size in `Cell` may cause misalignment in the regatta detail grid.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: N/A.

## External consumers

None known.
