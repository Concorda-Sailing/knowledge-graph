---
node_id: concorda-api::schemas/profile.py::BoatCreate
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9ff663a4de66381bab050015a3a277dbc2f8bd238abb972b92e60115fcdb9ba1
status: llm_drafted
---

# BoatCreate

## Purpose

The schema for creating a new boat entity. It is used by the `POST /api/profile/boats` endpoint to validate incoming payloads during boat registration. It is distinct from `BoatUpdate` (which allows all fields to be optional) and `BoatRead` (which includes system-generated fields like `id`, `created`, and `owner_ids`).

## Invariants

- **`sail_number` is required.** Unlike other fields in this schema, it has no default and is not `Optional`.
- **`positions` expects a list of dicts.** This field is used for spatial/positional data and must follow the structure expected by the downstream consumer.
- **`length` and `draft` are floats.** They are optional but must be numeric if provided.
- **`needs_handicap_help` defaults to `False`.**

## Gotchas

- **`achievements` coercion.** The `_achievements_legacy` validator (via `_coerce_achievements`) is used to handle legacy data formats during the creation flow to ensure compatibility with newer structured achievement types.
- **Registration rate limits.** Per commit `8b9722a`, the registration process is subject to dynamic rate limiting; ensure any automated testing of boat creation accounts for this.

## Cross-cutting concerns

- **Auth**: Handled by the `POST /api/profile/boats` router.
- **Rate limit**: Subject to the dynamic registration rate limit introduced in `8b9722a`.
- **Side effects**: Creating a boat via this schema triggers updates to the boat finder and potentially affects the visibility of the boat in crew/club lists.

## External consumers

- `POST /api/profile/boats` (via `routers/profile.py:659`)
