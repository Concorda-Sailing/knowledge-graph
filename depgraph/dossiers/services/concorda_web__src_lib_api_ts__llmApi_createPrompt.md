---
node_id: concorda-web::src/lib/api.ts::llmApi.createPrompt
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ae6bfff4c3c1e37b11429e356ffbf516e063917ef3186eb8be1f96566b0c9e7a
status: llm_drafted
---

# llmApi.createPrompt

## Purpose

Provides the client-side interface for managing LLM prompts via the administrative API. It allows for the creation, retrieval, updating, and deletion of prompts used by the system's AI features. Use this when building or modifying the administrative UI for prompt engineering.

## Invariants

- **Method is `POST`** — `createPrompt` uses a POST request to `/api/admin/llm-prompts`.
- **Payload excludes system fields** — The input `data` must be an `Omit<LLMPrompt, "id" | "created" | "modified">` to prevent clients from attempting to set immutable metadata.
- **Uses `fetchApiAuthenticated`** — All calls require a valid bearer token and will fail if the user lacks administrative privileges.
- **Returns full `LLMPrompt`** — Successful creation returns the complete object including the server-generated `id` and timestamps.

## Gotchas

- **Admin-only access** — Because this uses `fetchApiAuthenticated` against an `/api/admin/` path, any UI component using this method must be protected by an admin-role check to prevent unauthorized access attempts.

## Cross-cutting concerns

- **Auth**: Requires administrative privileges via `fetchApiAuthenticated`.
- **Audit**: N/A
- **Rate limit**: N/A
- **Side effects**: Changes to prompts via this API will immediately affect the behavior of LLM-driven features in the dashboard or member views.

## External consumers

- `concorda-web::src/app/members/admin/llm/page.tsx::PromptDialog`
