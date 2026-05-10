---
node_id: concorda-api::utils/llm_client.py::vision_completion
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 029ce0a66c8db33ad02dbba1b8ecbe877c038e66f08c1eb6bd80778a9a4ffc6e
status: current
---

# vision_completion

## Purpose

Sends a multimodal request (text prompt + image URL) to the configured LLM provider. It is a specialized wrapper around `chat_completion` that automatically constructs the multi-part message payload required for vision-capable models. Use this instead of `chat_completion` when you need to process image inputs.

## Invariants

- **Requires context** — Must be provided with either a `db` (Session) or a `config` dictionary, otherwise it raises a `RuntimeError`.
- **Input format** — The `image_url` must be a valid, reachable URL string.
- **Output type** — Returns a raw `str` containing the model's text response.
- **Model selection** — The model used is determined by the `vision_model` key within the provided `config`.

## Gotchas

- **Connection exhaustion** — Per commit `8b2e30a`, the LLM interaction patterns in this module can lead to connection-pool exhaustion; ensure any calling code handles potential timeouts or connection-pool-related errors gracefully.
- **Configuration dependency** — If `db` is passed, the function relies on `get_llm_config(db)` to resolve the `vision_model` name; if the database session is closed or the config is malformed, the call will fail.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
