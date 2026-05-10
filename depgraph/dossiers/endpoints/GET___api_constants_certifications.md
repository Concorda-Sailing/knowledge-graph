---
node_id: GET::/api/constants/certifications
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: e0ac0ac588d63749573ee579134afc60f34d13a74a31c7df749a793e3f25f103
status: llm_drafted
---

# GET /api/constants/certifications

## Purpose

Returns the list of available certifications available within the organization. This is a static-data endpoint used to populate selection UI in registration and profile-management flows. It is distinct from `/experience-levels`, which provides the professional hierarchy for user profiles.

## Invariants

- **Returns a list of `Certification` objects.** The response shape is a JSON array of objects matching the `Certification` Pydantic model.
- **Data is sourced from the `CERTIFICATIONS` constant.** This is a module-level list defined in the same file.
- **HTTP Method is `GET`.**

## Gotchas

- **Manual instantiation required.** Every item in the list is explicitly cast via `Certification(**cert)`, meaning the dictionary keys in the `CERTIFICATIONS` constant must strictly match the `Certification` model fields to avoid `TypeError`.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
