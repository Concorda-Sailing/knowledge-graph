---
node_id: concorda-api::schemas/profile.py::SailingResumeUpsert
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 535e9e751339b189659cb7cab5878f505f21be062d1681e34f497def893a2823
status: llm_drafted
---

# SailingResumeUpsert

## Purpose

The schema for updating a user's sailing resume via the `/api/profile/sailing-resume` endpoint. It encapsulates personal sailing credentials, experience levels, and professional identifiers (US/World Sailing) to build a comprehensive profile for crew matching and verification. Use this instead of `PersonRead` when the client needs to update specific sailing-related metadata without touching core identity fields.

## Invariants

- **`person_id` is implicit.** The identity is inferred from the authenticated session; the schema does not (and should not) accept a `person_id` in the request body.
- **`achievements` uses legacy coercion.** The field is processed via `_achievements_legacy` which calls `_coerce_achievements` to ensure compatibility with older data structures.
- **All fields are `Optional`.** This is an upsert schema; the client may send partial updates without providing the full profile.

## Gotchas

- **Credential field expansion.** Per commit `f311f7a`, this schema was recently expanded to include `us_sailing_number`, `world_sailing_id`, and `world_sailing_group`. Ensure any client-side forms are updated to support these new credential fields.
- **Null safety in validators.** Per commit `03a6819`, the system is sensitive to null values in profile-related fields; ensure that the `ProfileRead` validator (the read-side counterpart) is capable of filling defaults to prevent crashes when these fields are missing.
- **Legacy achievement format.** The `achievements` field relies on `_coerce_achievements` (via `_achievements_legacy`) to handle incoming data, implying the input shape might not always match the current `NotableRace` or `Achievement` models directly.

## Cross-cutting concerns

- **Auth**: Requires an authenticated session to infer the `person_id`.
- **Rate limit**: Subject to the dynamic registration rate limit introduced in commit `8b9722a`.
- **Side effects**: Updates to this schema (specifically `preferred_oa_ids` and experience levels) impact the visibility and matching logic for the crew finder service.

## External consumers

- Web/Mobile client for profile management.
