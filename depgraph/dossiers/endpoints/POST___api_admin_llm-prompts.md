---
node_id: POST::/api/admin/llm-prompts
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 34e1ca05c04dd646a9cf71862ae84963f5342b5adb0a250c31f16c9d306fbdae
status: llm_drafted
---

# POST /api/admin/llm-prompts

## Purpose

Provides the administrative interface for creating and managing LLM prompt templates. This endpoint allows admins to define the system instructions and context used by the AI agent plugin to ensure consistent behavior across the platform. It is distinct from the email template endpoints in the same file, as it manages the logic-heavy prompts used for AI-driven automation rather than human-readable email content.

## Invariants

- **Method is POST** and returns `status_code=201`.
- **Requires `_require_admin` dependency**; only users with administrative privileges can access this endpoint.
- **Prompt names must be unique.** The function raises a `409 Conflict` if a prompt with the same name already exists in the database.
- **Returns `LLMPromptRead` shape**, which includes the generated `id` and the full prompt content.

## Gotchas

- **Admin-only access is strict.** Because this is a sensitive administrative endpoint, any changes to the `_require_admin` dependency or the user permission model could break the ability to manage AI behavior.
- **Recent history shows high volatility in admin-user-related endpoints.** Commit `5b632f2` and `0f9d4ad` show a pattern of attempting to implement user deactivation/reactivation and subsequent reverts. While this endpoint is for prompts, the underlying `_require_admin` guard is subject to these frequent permission-logic shifts.

## Cross-cutting concerns

- **Auth**: Protected by `_require_admin`.
- **Side effects**: Used by the "AI agent plugin" (per commit `781b857`) to drive automated platform actions.

## External consumers

- `concorda-web::src/lib/api.ts::llmApi.createPrompt` (via `http_call`).
