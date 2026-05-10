---
node_id: concorda-api::utils/llm_client.py::get_llm_config
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8041df41ec0c31b62707fe828f98c45c3de2915ad8966aba28d5c9f012f9d8b7
status: llm_drafted
---

# get_llm_config

## Purpose

Fetches the active LLM configuration from the database to provide provider-specific credentials and model selection. It acts as the configuration layer for `chat_completion`, ensuring that the application uses the current active provider (defaulting to Groq) and the correct model for both text and vision tasks.

## Invariants

- **Returns a dictionary** containing `provider`, `api_key`, `base_url`, `model`, and `vision_model`.
- **Falls back to hardcoded defaults** (`DEFAULT_BASE_URL`, `DEFAULT_MODEL`, `DEFAULT_VISION_MODEL`) if no active `LLMConfig` is found in the database.
- **Requires an active record** where `is_active == True` to use custom credentials.
- **`vision_model` fallback logic:** If `vision_model` is not explicitly set in the DB, it defaults to the value of `model`.

## Gotchas

- **Connection-pool exhaustion risk:** Per commit `8b2e30a`, passing a raw `db: Session` directly into `chat_completion` can hold the database connection open during the long-running upstream HTTP request. Agents should prefer generating a `config` dict via `get_llm_config` first, then passing that dict to `chat_completion` to avoid blocking the DB pool.
- **Exponential backoff on 429s:** The `chat_completion` function implements a 4-attempt retry logic with exponential backoff (`2 ** attempt`). This is critical for stability when hitting Groq rate limits.

## Cross-cutting concerns

- **Auth**: Uses the `api_key` from the returned config to populate the `Authorization: Bearer` header.
- **Rate limit**: Implements a retry loop for HTTP 429 responses.
- **Side effects**: None.

## External consumers

None known.
