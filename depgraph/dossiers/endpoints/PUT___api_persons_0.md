---
node_id: PUT::/api/persons/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ce0cb2462fddbc066688acd82883a55058c4755db9f6ef26e2da8bbc82f67cdb
status: llm_drafted
---

# PUT /api/persons/{person_id}

## Purpose

Updates an existing person's profile data in the database. It performs a partial update by mapping fields from the `PersonCreate` model onto the existing `Person` record. Use this endpoint when a user needs to modify their own profile or when an admin is adjusting user attributes.

## Invariants

- **Requires `_require_admin` dependency** — Only users with administrative privileges can call this endpoint.
- **Input is `PersonCreate`** — The request body must match the schema for creating/updating a person.
- **Returns `PersonRead`** — The response is the fully updated `Person` object, including the database-generated ID and any system-managed fields.
- **Partial updates via `setattr`** — The function iterates through the provided model's items to update the existing record.

## Gotchas

- **Security/PII Leakage** — Per commit `33a37a3`, this endpoint is a high-risk area for PII/privilege gaps. Ensure that the `PersonCreate` model used here does not allow a user to escalate their own roles or modify sensitive fields that should be admin-only.
- **Broadcast side effect** — This method triggers a `PERSON_UPDATED` event via `broadcast_event`. Any system listening for this event must be prepared to handle a change in person metadata.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Websocket**: Emits `PERSON_UPDATED` event.
- **Audit**: N/A.
- **Rate limit**: none.
- **Side effects**: Updates to person data may affect any UI component or service relying on real-time person metadata via the `PERSON_UPDATED` broadcast.

## External consumers

None known.
