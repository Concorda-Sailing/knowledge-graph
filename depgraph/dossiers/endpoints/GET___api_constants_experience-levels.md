---
node_id: GET::/api/constants/experience-levels
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9537cfbd7d478981fb53e0484f4b875e8f855aec6a0b41f7f2ba2ca747e460d0
status: llm_drafted
---

# GET /api/constants/experience-levels

## Purpose

Returns the list of available experience levels used for crew registration and profile building. It transforms the internal `EXPERIENCE_LEVELS` constant into a list of `ExperienceLevel` objects to ensure the frontend receives structured data rather than raw strings. Use this when building forms or filters that require a standardized set of skill-based categories.

## Invariants

- **HTTP Method:** `GET`
- **Path:** `/api/constants/experience-levels`
- **Return Shape:** A JSON list of `ExperienceLevel` objects (e.g., `[{ "id": "...", "label": "..." }]`).
- **Data Source:** Derived from the `EXPERIENCE_LEVELS` constant in the same module.

## Gotchas

- **Schema expansion:** Per commit `1f4c4a6`, the list is not just strings but structured objects. Adding a new level requires ensuring it matches the `ExperienceLevel` Pydantic model, or the response will fail validation.

## Cross-cutting concerns

- **Auth:** None.
- **Websocket:** None.
- **Audit:** N/A.
- **Rate limit:** None.
- **Side effects:** Used by the crew registration flow to populate experience selection dropdowns.

## External consumers

- `concorda-web` (via `constantsApi.getExperienceLevels`)
