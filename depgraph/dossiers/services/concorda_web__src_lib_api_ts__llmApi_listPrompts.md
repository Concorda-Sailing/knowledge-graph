---
node_id: concorda-web::src/lib/api.ts::llmApi.listPrompts
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: fcb214cc003e8307602fac4b46ca4345f1fd5ec895c37f2eceb5271b6f91c944
status: llm_drafted
---

# llmApi.listPrompts

## Purpose

Provides the administrative interface for managing LLM prompt templates used by the system. It handles the retrieval, creation, updating, and deletion of `LLMPrompt` objects via the `/api/admin/llm-prompts` endpoint. Use this when building or modifying the administrative configuration UI for AI-driven features.

## Invariants

- **Uses `fetchApiAuthenticated`** — all calls require a valid bearer token.
- **Returns `LLMPrompt[]` for `listPrompts`** — the list is a collection of prompt templates.
- **`createPrompt` and `updatePrompt` use `Omit` types** — they explicitly exclude `id`, `created`, and `modified` to prevent client-side attempts to overwrite server-managed metadata.
- **Endpoint path is static** — `/api/admin/llm-prompts`.

## Gotchas

- **Admin-only access** — because these methods hit `/api/admin/*`, they are strictly gated by the backend's admin role check.
- **Schema-matching dependency** — per commit `bf15808`, the system is sensitive to shape-matching; ensure that any data passed to `createPrompt` or `updatePrompt` strictly adheres to the `LLMPrompt` interface to avoid silent failures or type mismatches during serialization.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin-level credentials).
- **Rate limit**: none.
- **Side effects**: Changes to prompts via `createPrompt`, `updatePrompt`, or `deletePrompt` will immediately affect the behavior of any LLM-driven features in the dashboard or regatta views that consume these prompts.

## External consumers

- `LLMConfigPage` in `src/app/members/admin/llm/page.tsx`.

## Open questions

- Should there be a specific `getPromptById` helper if the admin UI needs to drill down into a single prompt's configuration, or is the list/update pattern sufficient?
