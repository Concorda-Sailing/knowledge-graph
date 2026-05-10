---
node_id: concorda-api::models/llm_prompt.py::LLMPrompt
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 96bf3d240e7ae264ff5b08ca7445e4dd84a8496bb36d5dd1385dc1b2ade2c0df
status: current
---

# LLMPrompt

## Purpose

Backend SQLAlchemy model for admin-editable LLM prompt templates that drive Concorda's document-extraction features (`parse_nor_si`, `parse_social_event`, etc.). Each row is one prompt slug (`name`) plus a `system_prompt`, an optional `user_prompt_template` containing `{variables}`, and per-prompt LLM knobs (`model_override`, `temperature`, `use_vision`). Extraction services look up the active row by slug, snapshot it into a plain dataclass, and feed it to `utils.llm_client`. The point of the table is to let admins tune prompts via the admin UI without code deploys — copy/instructions for the model live in the DB, not in Python literals.

## Invariants

- `name` is unique and is the public lookup key — services hard-code slugs (`"parse_nor_si"`, `"parse_social_event"` in `services/nor_extract.py`) and look up by name, not by id.
- Only `is_active=True` rows are considered by extractors; `load_extract_prereqs` raises `NORExtractError("Prompt '...' not configured.")` if the active row is missing.
- `user_prompt_template` uses Python `str.format` placeholders (`{document_type}`, `{content}`) — not Jinja `{{var}}` like `EmailTemplate`. A literal `{` in prompt copy will break `.format()`.
- `system_prompt` is required; `user_prompt_template` is optional and falls back to `"Parse this {document_type}: {content}"` in `nor_extract.py`.
- `LLMPrompt.__init__` hard-codes `type="LLMPrompt"` for the polymorphic `BaseModel` — callers must not pass `type=`.
- `temperature` and `model_override` are per-prompt overrides; `None` means "use the global `LLMConfig` default". `nor_extract` substitutes `0.1` when temperature is null.

## Gotchas

- Rows are seeded by migrations `025_llm_prompts.py` (NOR/SI) and `033_social_event_prompt.py` (social). Editing prompt copy inside those migration files after they've run on prod has no effect — write a new migration that updates by `name`, and prefer update-if-exists over insert so admin edits aren't clobbered (deploys must not mutate data).
- `llm_prompts` is NOT in `tests/conftest.py`'s `_PRESERVE_TABLES` (only `schema_migrations` and `email_templates` are). The per-test wipe drops these rows, so any test that hits an extraction path needs to reseed or stub.
- The extractor's snapshot pattern (`_PromptSnapshot`) exists specifically so the DB session can be released before the multi-second LLM round-trip — don't refactor callers to hold the live ORM object across `chat_completion`/`vision_completion`, or you'll pin a pooled connection for the full network call.
- `use_vision=True` switches the request to `vision_completion` and rebuilds the prompt as `f"{system}\n\n{user}"` (single user-role message with an image), not the two-message chat shape — vision-mode prompts need to read as one self-contained instruction.
- Admin endpoints (`/api/admin/llm-prompts/*`) use no schema versioning. A bad edit goes live instantly on the next extraction request.

## Cross-cutting concerns

- Sole input to `services/nor_extract.py::load_extract_prereqs`, consumed by `routers/nor.py` (`POST /api/nor/extract/{file_id}`) and `scripts/season_bundle/extract.py`. Failures bubble up as `NORExtractError` and surface to the user as a 4xx on the NOR extract endpoint.
- Admin CRUD at `/api/admin/llm-prompts` is gated by `_require_admin`; there is no audit log on edits — changes to prompt copy are invisible after the fact (no `ActivityLog` write).
- No rate limiting on extraction calls; a poorly-tuned prompt that drives long completions costs real money on each invocation.

## External consumers

None directly. All reads happen server-side via the extraction services; the admin web UI is the only external editor and goes through the admin router.

## Open questions

- Should prompt edits write to `ActivityLog` (or a dedicated revision table) so a regression in extraction quality can be traced back to a specific admin change?
- `LLMConfig` is global (single API key + default model) but `LLMPrompt` allows per-row `model_override`. If multi-org LLM config ever lands, prompt selection probably needs an `organization_id` scope too.
