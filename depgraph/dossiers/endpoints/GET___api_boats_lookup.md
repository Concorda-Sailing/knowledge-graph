---
node_id: GET::/api/boats/lookup
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ea205cef96c706c5cd55225a7316b7f1b781878610c0737c152985a673677d00
status: llm_drafted
---

# GET /api/boats/lookup

## Purpose

Provides a way to identify a boat's UUID using a combination of its sail number and name. This is a critical lookup utility used when a user (or an external system) knows the human-readable identifiers but not the internal UUID. It is distinct from the `/{boat_id}/crew` endpoints because it is a discovery mechanism rather than a membership-based retrieval.

## Invariants

- **Requires `require_auth`** — The request must include a valid authentication token.
- **Requires two query parameters** — Both `sail_number` and `boat_name` are mandatory and must have a minimum length of 1.
- **Returns a specific shape** — On success, returns `{exists: true, boat_uuid: str, boat_name: str, owner_names: list[str]}`.
- **Uses `_normalize` for comparison** — The lookup is not a strict string match; it uses a normalization function to ensure whitespace or casing differences in the query don't prevent a match.

## Gotchas

- **Strict Route Ordering** — Per the source comment, this endpoint must be defined before any `/{boat_id}` routes. If it is moved below the parameterized routes, the router will attempt to treat the `lookup` string as a `boat_id`, causing a 404 or a type error.
- **Normalization dependency** — Because it relies on `_normalize` (as seen in `_normalize(b.name or "")`), the accuracy of the lookup depends on how aggressively that function strips characters.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth`.
- **Side effects**: Used by the `concorda-web` boat discovery flows to resolve names to IDs before initiating crew-related actions.

## External consumers

- `concorda-web::src/lib/api.ts::boatApi.lookup`
- `concorda-test::lib/api-client.ts::ApiClient.lookupBoat`
