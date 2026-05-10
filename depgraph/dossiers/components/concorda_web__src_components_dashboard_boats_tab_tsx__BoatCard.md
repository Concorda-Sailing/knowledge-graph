---
node_id: concorda-web::src/components/dashboard/boats-tab.tsx::BoatCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3bd5accc3fd103f9f61f2c1e2411d0fb45215bc4a3d8a1ef8686ba06767da3e9
status: current
---

# BoatCard

## Purpose

Renders a summary card for an individual boat within the dashboard's Boats tab. It provides a visual entry point (image or placeholder) and essential metadata like sail number and role-based status. Use this component when displaying a list of boats where the user needs to distinguish between owned vessels and those they are currently crewing.

## Invariants

- **`displayName` fallback**: If `name` is undefined, the component must use `sailNumber` to ensure the card is never visually empty.
- **Role-based Badge**: The `role` prop determines the badge variant (`default` for Owner, `secondary` for Crew) and dictates whether the `crewCount` sub-section is rendered.
- **Navigation**: The entire card is wrapped in a `Link` pointing to `/members?tab=boats&boat=${id}`, ensuring a consistent drill-down pattern to the boat detail view.
- **Image handling**: If `pictureUrl` is missing, a gradient placeholder with a `Sailboat` icon is rendered to maintain layout stability.

## Gotchas

- **Layout shifts on desktop**: Per commit `d361d6e`, the card was adjusted to ensure it spans full width on desktop within the Boats grid to prevent awkward whitespace in the dashboard layout.
- **Visual hierarchy**: Per commit `986abe0`, the component was refactored to be "picture-first," meaning the image/placeholder is the dominant visual element, and the `crewCount` is a secondary detail at the bottom.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Rebuilds/updates when the boat's `crewCount` or `missingCount` changes in the dashboard view.

## External consumers

None known.
