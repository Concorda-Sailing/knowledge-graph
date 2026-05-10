---
node_id: concorda-api::services/nor_extract.py::load_extract_prereqs
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 560b565de5d16baaf392e85a52ab81492b80420fe6cf442120b52aa9d969679f
status: current
---

# load_extract_prereqs

## Purpose

Fetches the necessary LLM configuration and prompt templates from the database to prepare for a NOR (Notice of Race) or SI (Sailing Instructions) extraction. It is designed to decouple the database session from the long-running LLM network call by returning a `_PromptSnapshot` and a config dictionary. An agent should use this method to prepare data before closing a DB session, then pass the results to `extract_nor_from_bytes_pure` to avoid holding a connection open during the API call.

## Invariants

- **Returns a 4-element tuple**: `(prompt_snapshot, ll_config, doc_type_label, prompt_name)`.
- **Requires a valid `document_type`**: Must be either `"social"` or `"nor"`/`"si"` to determine the correct `prompt_name`.
- **Throws `NORExtractError`**: Raised if the `LLMPrompt` is missing/inactive or if the `api_key` is missing from the config.
- **`prompt_name` mapping is hardcoded**: `"social"` maps to `parse_social_event`; any other value defaults to the `parse_nor_si` logic.

## Gotchas

- **Connection pool exhaustion risk**: If the caller uses the standard `extract_nor_from_bytes` instead of this "load-then-pure" pattern, the DB connection is held for the duration of the LLM call. This was addressed in commit `8b2e30a` to resolve connection-pool exhaustion.
- **Strict prompt requirements**: If the `LLMPrompt` in the DB is not marked as `is_active == True`, this method will raise a `NORExtractError`.

## Cross-cutting concerns

- **Auth**: None (relies on the caller's `db: Session` and the existence of an `api_key` in the config).
- **Side effects**: Directly used by `POST /api/nor/extract/{0}` to drive the extraction pipeline.

## External consumers

- `POST /api/nor/extract/{0}` (via `routers/nor.py`).
