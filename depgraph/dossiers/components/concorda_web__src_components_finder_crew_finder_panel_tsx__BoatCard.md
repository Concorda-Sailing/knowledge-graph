---
node_id: concorda-web::src/components/finder/crew-finder-panel.tsx::BoatCard
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 51f510eb4397cb4fb61a56875b374671b4f497b2b23fc51f7a3af3343c31b6fe
status: current
---

# BoatCard

## Purpose

Renders a summary card for a boat profile within the Crew Finder interface. It provides a high-level overview of the vessel (name, class, manufacturer, length, and sail number) alongside key status indicators like "Accepting Crew" and available positions. It serves as a navigational entry point, redirecting users to the detailed boat profile page via `router.push` or the internal `Link`.

## Invariants

- **Navigation is a full-card click.** The `Card` component uses an `onClick` handler that intercepts clicks, unless the user clicks a nested `a` or `button` (e.g., for contact actions).
- **Display fallback for names.** If `profile.boat_name` is missing, the component renders `profile.sail_number` as the primary title.
- **Input type is `BoatCrewfinderProfile`.** The component expects a structured profile object containing boat metadata and availability status.
- **Navigation target is `/members/crewfinder/boat/${profile.boat_id}`.**

## Gotchas

- **Event bubbling prevention.** The `onClick` handler on the `Card` includes a check `(e.target as HTMLElement).closest("a, button")` to ensure that clicking a specific action button (like "Contact") doesn't trigger the card's navigation. Without this, clicking a button would trigger both the button's action and the router push.
- **Layout stability.** Per commit `f36708e`, card footers and button alignments were specifically adjusted to ensure consistent vertical spacing in the finder grid.

## Cross-cutting concerns

- **Auth**: None.
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: N/A.
- **Side effects**: Part of the `BoatFinderPanel` layout; changes to this component's height or structure can affect the grid alignment of the entire finder page.

## External consumers

None known.
