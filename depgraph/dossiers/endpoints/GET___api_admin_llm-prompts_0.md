---
node_id: GET::/api/admin/llm-prompts/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 3650c45adec321d0b30e2a426f9ca6dbd1fec06ca5e43f9ded664db1ddc80267
status: llm_drafted
---

# GET /api/admin/llm-prompts/{prompt_id}

## Purpose

Retrieves a single LLM prompt by its unique identifier. This endpoint is part of the administrative suite used to manage the system prompts that drive AI agent behaviors. An agent should use this specific endpoint when it needs to fetch the current configuration for a specific prompt rather than listing all available prompts.

## Invariants

- **Requires `_require_admin` dependency** — Access is restricted to users with administrative privileges.
- **Returns `LLMPromptRead` shape** — The response includes the `id`, `name`, `body`, and `sort_order`.
- **Throws 404 if not found** — If the `prompt_id` does not match an existing record, the API returns a 404 error.
- **Strictly GET** — This specific node is a read-only operation; mutations are handled by the sibling POST/PUT/DELETE endpoints in the same router.

## Gotchas

- **Admin privilege escalation check** — Per commit `650233f`, all admin endpoints in this router are subject to strict privilege escalation blocking; ensure any changes to the dependency logic do not bypass `_require_admin`.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` (Admin role).
- **Rate limit**: None (Admin-only endpoints are not subject to the standard user rate limits).
- **Side effects**: Changes to the underlying `LLMPrompt` data (via sibling endpoints) will change the behavior of the AI agent plugin.

## External consumers

- `concorda-web::src/lib/api.ts::llmApi.getPrompt`
