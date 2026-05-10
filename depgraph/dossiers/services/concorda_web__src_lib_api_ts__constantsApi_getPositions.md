---
node_id: concorda-web::src/lib/api.ts::constantsApi.getPositions
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bb0757e9aaa047ff119a84bef28837101e01efa8c7af0b683abb16cc3ace61d7
status: current
---

# constantsApi.getPositions

## Purpose

Fetches the list of available roles/positions from the constants endpoint. This is a read-only, unauthenticated call used to populate selection menus (e.g., for crew or boat roles) to ensure the frontend stays in sync with the backend's valid enumeration of positions.

## Invariants

- **Returns a `string[]`** of position names.
- **Uses `fetchApi`** (unauthenticated) to access the `/api/constants/positions` endpoint.
- **Does not require a bearer token**, making it safe for use during initial app load or pre-login states.

## Gotchas

- **Avoid coupling to position names in logic.** Per commit `b4d60c6`, the system recently dropped "position-name gating" to avoid brittle logic where the UI depends on specific string values from this endpoint. Use these strings for display/selection, but do not rely on them for business logic branching.

## Cross-cutting concerns

- **Auth**: none (unauthenticated).
- **Websocket**: none.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Used to populate selection UI for crew and boat-related forms.

## External consumers

None known.
