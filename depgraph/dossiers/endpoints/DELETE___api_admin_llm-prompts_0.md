---
node_id: DELETE::/api/admin/llm-prompts/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 19b3eba4f6d27a621e966c3e49c84cfdc1ec4084a38d86af51d712f81eec0488
status: llm_drafted
---

# DELETE /api/admin/llm-prompts/{prompt_id}

## Purpose

Deletes a specific LLM prompt from the database by its ID. This is an administrative endpoint used to prune outdated or incorrect prompt templates that are being used by the AI agent plugin.

## Invariants

- **Method is `DELETE`** — targeting the `/api/admin/llm-prompts/{prompt_id}` path.
- **Requires `_require_admin` dependency** — only users with administrative privileges can execute this.
- **Returns 404 if `prompt_id` does not exist** — the function explicitly checks for the existence of the prompt before attempting deletion.
- **Returns a success message** — on successful deletion, returns `{"message": "Prompt deleted"}`.

## Gotchas

- **Security sensitive** — per commit `650233f`, there is a focus on blocking privilege escalation in admin user endpoints; ensure this endpoint remains strictly guarded by `_require_admin` to prevent unauthorized prompt manipulation.

## Cross-cutting concerns

- **Auth**: Requires `_require_admin` dependency.
- **Side effects**: Deleting a prompt may break the AI agent plugin functionality if the plugin expects that specific prompt to exist for its logic.

## External consumers

- `concorda-web::src/lib/api.ts::llmApi.deletePrompt`
