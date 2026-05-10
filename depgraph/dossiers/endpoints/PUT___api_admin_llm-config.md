---
node_id: PUT::/api/admin/llm-config
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6b9a57a4ddf88f49971dd89ce144bc48326b09b71e934f652b20f57999162874
status: llm_drafted
---

# PUT /api/admin/llm-config

## Purpose

Updates the global LLM configuration, including the provider, base URL, and model identifiers. It serves as the central control for the AI agent's behavior and connectivity. Use this endpoint when changing the underlying LLM provider (e.g., switching from Groq to another OpenAI-compatible API) or updating the specific model string used for vision-capable tasks.

## Invariants

- **Requires System Admin privileges** — The function calls `_require_system_admin(current_user)` after the initial `_require_admin` check.
- **Returns `LLMConfigResponse`** — The response includes `provider`, `base_url`, `model`, `vision_model`, `is_active`, and a boolean `has_api_key`.
- **Idempotent creation** — If no `LLMConfig` record exists in the database, the method creates a default configuration using `groq` and `llama-4-scout-17b-16e-instruct` as fallbacks.
- **Partial updates via `exclude_unset=True`** — Only the fields explicitly provided in the `LLMConfigUpdate` payload are mutated on the existing config object.

## Gotchas

- **Privilege Escalation Guard** — Per commit `650233f`, there is a strict requirement to ensure that only users with elevated permissions can access this endpoint to prevent unauthorized configuration changes.
- **Default Fallbacks** — If `provider` or `base_url` are not provided in the payload, the function defaults to `groq` and `https://api.groq.com/openai/v1` respectively.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` (dependency) and `_require_system_admin` (explicit check).
- **Rate limit**: none
- **Audit**: Y (updates global system configuration)
- **Side effects**: Changes to this config will immediately affect the behavior of any AI agent or LLM-driven feature-set (e.g., automated event summaries or automated crew notifications) that relies on the global model/provider.

## External consumers

- `concorda-web`: `LLMConfigPage` (via `http_call` at `page.tsx:82`).
