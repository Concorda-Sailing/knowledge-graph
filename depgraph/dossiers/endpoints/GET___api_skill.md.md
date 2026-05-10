---
node_id: GET::/api/skill.md
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2371b5bee60c9457c36bf15f90c6ffe8e309fdae254c72b3a57ae6871399862d
status: current
---

# GET /api/skill.md

## Purpose

Returns the raw Markdown content of the `SKILL.md` manifest file. This file serves as the system prompt/instruction set for the AI agent, defining its persona, capabilities, and operational boundaries. This endpoint is used by the agent orchestration layer to inject context into the LLM session.

## Invariants

- **Returns `text/markdown`** — the `media_type` is explicitly set to `text/markdown; charset=utf-8`.
- **File path is absolute-relative** — it resolves from the `agents.py` location to the `skills/concorda-portal/SKILL.md` directory.
- **Returns 404 if file is missing** — if the physical file does not exist at the resolved path, it raises an `HTTPException`.
- **Cache-Control is 5 minutes** — the response includes `max-age=300` to allow downstream proxies to cache the prompt.

## Gotchas

- **File-system dependency** — because the endpoint reads directly from the disk via `_SKILL_PATH.read_text()`, any deployment issues involving the `skills/` directory structure will cause this endpoint to return a 404, effectively "lobotomizing" the agent's persona.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: The content of this file directly dictates the behavior of the AI agent plugin (see commit `781b857`).

## External consumers

The AI agent orchestration layer (internal to the API).
