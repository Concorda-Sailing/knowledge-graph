---
node_id: concorda-api::utils/llm_client.py::chat_completion
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4fa513326e62f507d422a253d03ee7b3ca5b1958f6799ee5d465739b118e58f0
status: llm_drafted
---

# chat_completion

## Purpose

The primary interface for interacting with the configured LLM provider (currently Groq). It abstracts the construction of the payload, header management, and retry logic for both standard text-based chat completions and vision-based requests. Use `chat_completion` for standard text flows and `vision_completion` when an image URL is required.

## Invariants

- **Requires configuration context.** Either a `db` session (to fetch config via `get_llm_config`) or a pre-fetched `config` dictionary must be provided.
- **Returns a raw string.** The function returns the string content of the first message in the `choices` array.
- **Implements exponential backoff.** On a 429 (Rate Limit) error, the function performs up to 4 retries with a `2 ** attempt` sleep interval.
- **Strict payload structure.** The `messages` argument must be a list of dictionaries following the standard OpenAI/Groq chat completion format.

## Gotchas

- **Connection-pool exhaustion.** Per commit `8b2e30a`, this service was previously prone to exhausting connection pools; ensure any new calls or modifications respect the existing timeout and retry patterns to avoid blocking the event loop.
- **DB Session lifecycle.** If `db` is passed instead of `config`, the database session is held open for the duration of the upstream HTTP call (up to 120s). This can lead to connection starvation in high-concurrency scenarios.
- **API Key dependency.** If the `api_key` is missing from the configuration, a `RuntimeError` is raised. This is a hard failure if the admin has not configured settings in "Admin > LLM settings."

## Cross-cutting concerns

- **Auth**: Uses a Bearer token derived from the `api_key` in the `config` dictionary.
- **Rate limit**: Implements a 4-attempt exponential backoff for 429 status codes.
- **Side effects**: High-latency calls (up to 120s timeout) can block worker threads if not called within an async-friendly context or a separate thread.

## External consumers

None known.
