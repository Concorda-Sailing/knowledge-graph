---
node_id: concorda-api::models/llm_config.py::LLMConfig
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8d99c301de9b30fb4c44442f9d086b8db62cde93990820a7d932f3b6c587e41c
status: llm_drafted
---

# LLMConfig

## Purpose

Defines the database schema for LLM provider configurations. It stores credentials and endpoint metadata (provider, API key, base URL, and model names) required to route requests to OpenAI-compatible APIs like Groq or Anthropic. This model is the single source of truth for the application's generative AI routing logic.

## Invariants

- **`provider` defaults to `"groq"`** via the SQLAlchemy `default` parameter.
- **`is_active` is a boolean** with a `server_default="1"` to ensure the record is active upon creation.
- **`api_key` and `base_url` are nullable** to support providers that might use environment variables or local defaults.
- **`model` is a required string** with a default value of `"llama-4-scout-17b-16e-instruct"`.

## Gotchas

- **Commit `4d2a347`** introduced this model alongside its admin endpoints; any changes to the field types (like `String(500)`) must be coordinated with the admin router to avoid serialization errors in `routers/admin.py`.

## Cross-cutting concerns

- **Auth**: Managed via `GET::/api/admin/llm-config` and `PUT::/api/admin/llm-config` in `routers/admin.py`.
- **Audit**: N/A.
- **Side effects**: Changes to this model directly impact the behavior of all LLM-dependent services in the API.

## External consumers

None known.
