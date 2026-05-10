---
node_id: GET::/api/admin/llm-prompts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 010b4245e8169a5ed0a1587919a20ccbb401743d8eca8e2516c45f6a419347a3
status: current
---

# GET /api/admin/llm-prompts

## Purpose

Provides administrative CRUD operations for managing LLM prompt templates used by the AI agent plugin. This endpoint allows admins to define the system instructions, model overrides (like temperature or vision capabilities), and ordering for prompts used in automated workflows. It is the primary interface for tuning the behavior of the AI agent without redeploying code.

## Invariants

- **Requires `_require_admin` dependency** — all operations (GET, POST, PUT, DELETE) are restricted to administrative users.
- **Returns `LLMPromptRead` schema** — ensures consistent output for the `list` and `get` operations.
- **Ordering is deterministic** — the `list_llm_prompts` method orders by `sort_order` and then by `name`.
- **Name uniqueness is enforced** — attempting to create a prompt with an existing name results in a 409 Conflict.

## Gotchas

- **Privilege escalation risk** — per commit `650233f`, ensure any changes to this router do not inadvertently expose or allow modification of sensitive admin-only fields via the `LLMPromptUpdate` model.
- **Strict name validation** — the `create_llm_prompt` function checks for existing names; if a name is changed via `update_llm_prompt`, it does not currently re-validate uniqueness against the new name, which could lead to unexpected ordering or retrieval issues.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Side effects**: Changes to these prompts directly affect the behavior of the "AI agent plugin" (referenced in commit `781b857`).
- **Rate limit**: None explicitly defined for this endpoint, but subject to general admin router protections.

## External consumers

- `concorda-web` (via `llmApi.listPrompts`).
