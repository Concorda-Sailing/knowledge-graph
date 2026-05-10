---
node_id: GET::/api/constants/boat-config-templates
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c974bcb9a7fde3a947a3bc42bbcfc5d8e779d445a15cff6b6019015de04d0249
status: llm_drafted
---

# GET /api/constants/boat-config-templates

## Purpose

Returns the list of predefined crew configurations used to initialize boat diagrams. This endpoint provides the structural templates (e.g., "double-handed" or "full crew") that allow users to quickly set up a crew layout rather than building one from scratch. It is distinct from `get_certifications` or `get_position_locations`, which provide static data for different parts of the onboarding/setup flow.

## Invariants

- **Returns a list of objects.** The response is the raw `CONFIG_TEMPLATES` list.
- **Static data source.** This endpoint returns data from a module-level constant; it does not query a database.
- **No parameters required.** The endpoint accepts no query parameters or path variables.

## Gotchas

- **Template structure is tied to diagram support.** Per commit `74b26e5`, these templates were added specifically to support "position diagram" functionality. Any change to the shape of these templates must ensure compatibility with the frontend diagram renderer.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None known.

## External consumers

None known.
