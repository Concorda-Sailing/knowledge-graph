---
node_id: concorda-web::src/lib/api.ts::llmApi.getPrompt
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 99b796aa328e1f64f7e01bae834575582fca23d3520531b2218f98549b0736f7
status: current
---

# llmApi.getPrompt

## Purpose

Provides a programmatic interface for managing LLM prompts via the admin API. It allows for fetching, creating, updating, and deleting prompt templates used by the system's automated agents. Use this instead of manual API calls when building administrative tools or agent-configuration dashboards.

## Invariants

- **Requires administrative privileges** via `fetchApiAuthenticated`.
- **Returns a `LLMPrompt` object** for `getPrompt`.
- **`createPrompt` and `updatePrompt` exclude `id`, `created`, and `modified`** from the input payload to prevent accidental overwriting of system-generated metadata.
- **`deletePrompt` returns a `{ message: string }`** rather than the deleted object.

## Gotchas

- **Admin-only access.** Because this uses `fetchApiAuthenticated` against `/api/admin/llm-prompts`, calls will fail with 401/403 if the user lacks the necessary administrative roles.
- **Strict schema for updates.** `updatePrompt` uses `Partial<Omit<...>>`, meaning you cannot pass a new `id` or attempt to reset the `created` timestamp during an update.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level bearer token).
- **Rate limit**: none.
- **Audit**: N/A.

## External consumers

None known.
