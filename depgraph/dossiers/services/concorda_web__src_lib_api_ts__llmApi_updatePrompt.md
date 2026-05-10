---
node_id: concorda-web::src/lib/api.ts::llmApi.updatePrompt
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5dbf6be856f0866f174d49432f7a34e2965e33c07a0d6068e411c8b39b42a921
status: llm_drafted
---

# llmApi.updatePrompt

## Purpose

Provides the interface for updating existing LLM prompt templates in the admin dashboard. It specifically targets the `PUT` method to modify the content or configuration of a prompt identified by a unique ID. This is a specialized administrative tool used to refine the behavior of the system's AI-driven features.

## Invariants

- **Method is `PUT`** — Updates the existing resource at the specific endpoint.
- **Input is a `Partial` type** — The `data` argument must omit `id`, `created`, and `modified` fields to prevent accidental overwriting of immutable metadata.
- **Returns `LLMPrompt`** — The method returns the full, updated prompt object upon success.
- **Requires authentication** — Uses `fetchApiAuthenticated` to ensure only authorized administrators can modify system prompts.

## Gotchas

- **Metadata protection** — The use of `Omit<LLMPrompt, "id" | "created" | "modified">` is critical; attempting to pass an `id` in the body is a client-side type error, but the backend relies on this distinction to maintain record integrity.
- **Admin-only scope** — Because this relies on `fetchApiAuthenticated`, it is strictly tied to the admin permission level; any attempt to call this from a standard member context will result in a 401 or 403.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires admin privileges).
- **Side effects**: Updates to prompts via this method will immediately change the behavior of any LLM-driven features (e.g., automated event descriptions or crew suggestions) across the platform.

## External consumers

- `PromptDialog` in `src/app/members/admin/llm/page.tsx`.

## Open questions

- Should the API support a "dry run" or "preview" mode for prompt updates to allow admins to test a new prompt against existing data before committing the change to the live system?
