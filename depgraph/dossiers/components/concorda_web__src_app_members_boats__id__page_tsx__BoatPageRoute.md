---
node_id: concorda-web::src/app/members/boats/[id]/page.tsx::BoatPageRoute
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b6a952094bd634463218b0cecf5fcc26d6629fecb516019b8e3756e112f596c1
status: current
---

# BoatPageRoute

## Purpose

The entry point for the boat detail route. It extracts the `id` from the URL parameters and passes it to the `BoatPage` component. This serves as the thin wrapper required by Next.js App Router to bridge the dynamic route segment into the actual view logic.

## Invariants

- **`params.id` must be cast to a string.** The component relies on `useParams()` returning a value that satisfies the `boatId` prop requirement for `BoatPage`.
- **Client-side execution.** The `"use client"` directive is mandatory as it relies on the `useParams` hook from `next/navigation`.

## Gotchas

- **Role-based view splitting.** Per commit `4fad70e`, this route now serves two distinct views: one for the boat owner and one for active crew. Changes to the URL structure or parameter handling will break the conditional rendering logic inside `BoatPage`.
- **Responsive layout dependencies.** Per commit `bddd87c`, the boat page hero, avatar, and tab bar are highly sensitive to mobile/desktop breakpoints. Modifying the routing or the way `params` are passed can disrupt the responsive layout of the boat detail view.

## Cross-cutting concerns

- **Auth**: Indirectly relies on the authentication state of the user viewing the boat (Owner vs. Crew) to determine which view `BoatPage` renders.
- **Side effects**: Changes to this route affect the rendering of the boat hero, avatar, and tab bar components.

## External consumers

None known.
