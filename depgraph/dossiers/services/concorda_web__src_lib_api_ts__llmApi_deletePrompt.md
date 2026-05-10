---
node_id: concorda-web::src/lib/api.ts::llmApi.deletePrompt
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 96402e73ab15fc9fcd733c0bcdd775544c2af25ccf5ea0838d6e25e397d395fa
status: current
---

# llmApi.deletePrompt

## Purpose

Deletes a specific LLM prompt configuration from the admin backend. It is part of the `llmApi` object and is used to manage the lifecycle of prompts used by the system's AI agents. Use this method when an administrator needs to remove a prompt template that is no longer valid or required.

## Invariants

- **HTTP Method is `DELETE`** — follows standard RESTful patterns for resource removal.
- **Requires a valid `id`** — the string must match a specific prompt's unique identifier.
- **Uses `fetchApiAuthenticated`** — the request must include valid administrative bearer credentials.
- **Returns a success message** — the expected return shape is `{ message: string }`.

## Gotchas

- **Admin-only access** — because this uses `fetchApiAuthenticated` and hits an `/api/admin/` endpoint, it is strictly gated by administrative permissions.
- **Direct dependency** — `LLMConfigPage` (page.tsx:102) relies on this for its administrative interface; changes to the signature or return type will break the admin UI.

## Cross-cutting concerns

- **Auth**: Requires administrative bearer token via `fetchApiAuthenticated`.
- **Side effects**: Deleting a prompt may affect any automated agent workflows that rely on that specific prompt template for context or instruction.

## External consumers

- `LLMConfigPage` in `src/app/members/admin/llm/page.tsx`.
