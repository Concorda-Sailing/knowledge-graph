---
node_id: GET::/api/admin/llm-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c369eaaba643d8b849c596bf15805e26b40b5982c7de299366d841c23df690ea
status: llm_drafted
---

# GET /api/admin/llm-config

## Purpose

Retrieves the current configuration for the system's LLM provider (e.g., Groq), including the base URL, model names, and active status. This endpoint is used by the admin dashboard to display and manage the AI agent's operational parameters. It serves as the read-only counterpart to the `PUT` configuration endpoint.

## Invariants

- **Requires `_require_admin` dependency** — Access is restricted to users with administrative privileges.
- **Returns `LLMConfigResponse`** — The response shape includes `provider`, `base_url`, `model`, `vision_model`, `is_active`, and `has_api_key`.
- **Provides hardcoded defaults** — If no configuration exists in the database, it returns a default object with `provider="groq"` and `model="llama-4-scout-17b-16e-instruct"`.
- **`has_api_key` is a boolean derived from presence** — The field is a boolean check of whether `api_key` is truthy in the database.

## Gotchas

- **Fallback logic for `base_url`** — If the database record has a null `base_url`, the endpoint returns the hardcoded Groq URL (`https://api.groq.com/openai/v1`) rather than an empty string, ensuring the client doesn't receive a broken endpoint.
- **Dependency on `LLMConfig` existence** — The endpoint is designed to be safe even if the table is empty, returning a default configuration instead of a 404 or 500 error.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` via FastAPI dependency.
- **Side effects**: Changes to the configuration (via the sibling `PUT` endpoint) affect the behavior of the AI agent plugin mentioned in commit `781b857`.

## External consumers

- `concorda-web::src/app/members/admin/llm/page.tsx` (LLMConfigPage)
