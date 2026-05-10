---
node_id: concorda-api::models/regatta_intent.py::RegattaIntent
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: d3ce6290759a8c657dcdde7db06e750e9670cd514f69e8b33057eacf07cb0485
status: current
---

# RegattaIntent

## Purpose

The `RegattaIntent` model tracks a person's participation status for a specific regatta, either as a racer (racing) or a crew member (crewing). It serves as the bridge between a user and a regatta event, capturing their specific roles and required/offered positions. Use this model when building features related to regatta sign-ups, position matching, or availability tracking.

## Invariants

- **`regatta_uuid` and `person_uuid` are required.** Both must be valid 36-character UUID strings.
- **`intent` is a constrained string.** Valid values are strictly `"racing"` or `"crewing"`.
- **`status` defaults to `"interested"`.** Valid transitions are typically to `"confirmed"` or `"withdrawn"`.
- **`boat_uuid` is nullable.** This is required if the intent is `"racing"` but can be null during the initial `"interested"` phase.
- **`positions_needed` and `positions_offered` are JSON lists.** These store the specific roles/skills relevant to the user's intent.

## Gotchas

- **Model was recently added in commit `d77f83f`.** Because this is a new model, existing database migrations for `regatta_intents` must be verified against the `BaseModel` inheritance to ensure compatibility with the `concorda-api` global setup.

## Cross-cutting concerns

- **Auth**: None (though the API endpoints consuming this model likely require user authentication).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Directly impacts the data returned by `GET /api/boats/{0}/events` (routers/boats.py:1055).

## External consumers

- `GET /api/boats/{0}/events` (via `routers/boats.py`).
