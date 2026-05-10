---
node_id: concorda-web::src/components/finder/crew-finder-panel.tsx::ProfileGrid
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3535e5bb138945aa87ddb600964199b5ec2bbb16814e471a516a0bda859de157
status: current
---

# ProfileGrid

## Purpose

Renders the visual representation of crew profiles in either a grid or a list format. It serves as the primary display layer for the "Crew" tab within the unified finder interface, transforming `CrewfinderProfile` data into interactive elements (avatars, badges, and links). Use this component when you need to display a list of people rather than boats, as it handles the specific logic for person-based metadata like `experience_level` and `positions_preferred`.

## Invariants

- **Input types**: Accepts `crew` (array of `CrewfinderProfile`) and `boats` (array of `BoatCrewfinderProfile`).
- **View modes**: Supports exactly two modes: `"grid"` (standard for visual scanning) or `"list"` (standard for high-density data).
- **Navigation**: Links to person profiles use the pattern `/members/crew/${profile.person_id}`.
- **Fallback UI**: Displays a centered `Card` with an `Anchor` icon if both `crew` and `boats` arrays are empty.

## Gotchas

- **Layout stability**: Per commit `f36708e`, the layout requires careful management of card footers to ensure they pin to the bottom and maintain alignment when switching between grid and list views.
- **Component extraction**: This component is a result of the refactor in `10468ed` which moved bodies from the main finder page into specialized panel components to reduce complexity.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: The `onContact` callback triggers the `contactDialog` state in the parent `CrewFinderPanel`, which manages the visibility of the contact modal.

## External consumers

None known.
