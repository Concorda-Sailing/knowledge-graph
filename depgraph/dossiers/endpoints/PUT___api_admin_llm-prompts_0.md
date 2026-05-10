---
node_id: PUT::/api/admin/llm-prompts/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 9647a86f019d97d4646837b9c7ffae62c691cfb0d2d279745729823f62323a21
status: llm_drafted
---

# PUT /api/admin/llm-prompts/{prompt_id}

## Purpose

Provides an administrative interface to update existing LLM prompt configurations. This endpoint is used to modify the system prompts that drive AI-driven features, allowing for real-time tuning of agent behavior without code deployments. It is distinct from the creation endpoint (which handles full object instantiation) by utilizing `LLMPromptUpdate` to allow partial updates via `exclude_unset=True`.

## Invariants

- **Requires `_require_admin` dependency** — Only users with administrative privileges can access this endpoint.
- **Input is a partial update** — Uses `LLMPromptUpdate` to allow updating specific fields of an existing prompt.
- **Returns `LLMPromptRead`** — The response includes the fully updated object, including the `id`.
- **Atomic updates** — Changes are committed to the database via `db.commit()` immediately after the `setattr` loop.

## Gotchas

- **Admin privilege escalation risk** — Per commit `650234`, ensure that any changes to the `_require_admin` dependency or the underlying user model do not inadvertently allow non-admin users to access this endpoint.
- **Partial updates via `exclude_unset`** — Because the loop uses `data.model_dump(exclude_unset=True)`, only fields explicitly provided in the request body are mutated. If a field is omitted from the JSON, the existing value in the database remains unchanged.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Side effects**: Updates to these prompts directly affect the output of AI agent plugins and automated-response features.

## External consumers

- `concorda-web::src/lib/api.ts::llmApi.updatePrompt` (via string_url, fuzzy, api.ts:3258)
