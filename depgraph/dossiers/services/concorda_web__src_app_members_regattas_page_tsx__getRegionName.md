---
node_id: concorda-web::src/app/members/regattas/page.tsx::getRegionName
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0102288427ade5b5d39479030e6e937ec6dd600756750d63d65d99ae0984d891
status: current
---

# getRegionName

## Purpose

Resolves a human-readable region name from a `RegattaDetail` object. It acts as a fallback mechanism to ensure a location is displayed even when the primary Organizing Authority (OA) data is missing or incomplete. Use this when you need to display a location-based string that doesn't rely on the OA's specific region property.

## Invariants

- **Returns `string | undefined`**. Returns the `start_area_location` if present, otherwise returns `undefined`.
- **Fallback-driven**. It does not perform a lookup against a database or a Map; it is a pure extraction from the provided `regatta` object.
- **Decoupled from OA**. Unlike the `RegattaCard` logic which prioritizes `oas[0].region`, this function ignores the OA and looks directly at the venue's physical location string.

## Gotchas

- **Inconsistent Source of Truth**. Per the source comment, the `RegattaCard` component treats the OA's region as the single source of truth, whereas this function pulls from `start_area_location`. This creates a discrepancy where the "Region" displayed in a card might differ from the "Region" returned by this helper if the `start_area_location` is used instead.
- **Implicit Fallback**. If `start_area_location` is an empty string or null, the function returns `undefined`, which may cause the UI to render nothing rather than a placeholder.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
