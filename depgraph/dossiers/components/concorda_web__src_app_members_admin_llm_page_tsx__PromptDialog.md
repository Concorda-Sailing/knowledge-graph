---
node_id: concorda-web::src/app/members/admin/llm/page.tsx::PromptDialog
node_kind: component
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 373e5198181260a8c90848747633c560b31f1d014768d25b5bc0460349e0cf9c
status: llm_drafted
---

# PromptDialog

## Purpose

The `PromptDialog` is a modal interface for creating or editing LLM prompts (e.g., extraction or generation prompts). It handles the local state for a prompt's configuration—including name, display name, category, and model-specific parameters—and synchronizes this data with the `llmApi`. It serves as a unified form for both "New Prompt" and "Edit Prompt" modes based on the presence of a `prompt` object.

## Invariants

- **Mode switching is driven by `prompt` presence.** If `prompt` is truthy, the component performs an update via `llmApi.updatePrompt`; otherwise, it performs a creation via `llmApi.createPrompt`.
- **`temperature` is cast to a float.** The input is managed as a string in the local state but must be converted to a float via `parseFloat` before being sent to the API.
- **Optional fields are sent as `undefined`.** Fields like `description`, `user_prompt_template`, and `model_override` are explicitly set to `undefined` if empty to ensure the API receives the correct payload shape.
- **`onSuccess` is the terminal callback.** The dialog relies on the parent to handle the post-save lifecycle (e.g., closing the modal or refreshing a list).

## Gotchas

- **Mobile layout constraints.** Per commit `0564f06`, the dialog content uses `max-w-[calc(100vw-2rem)]` and `max-h-[90vh]` to prevent overflow issues on mobile devices when the keyboard or long forms are active.
- **State reset on `open` change.** The `useEffect` hook resets all local state (name, category, etc.) whenever the `open` prop or `prompt` prop changes. This ensures that if a user starts typing in a "New" prompt and then opens an "Edit" prompt without closing the dialog, the state doesn't leak.

## Cross-cutting concerns

- **Auth**: Relies on `llmApi` which requires an authenticated session.
- **Side effects**: Successful saves trigger `onSuccess`, which in the parent context (`page.tsx`) is expected to refresh the prompt list/table.

## External consumers

None known.
