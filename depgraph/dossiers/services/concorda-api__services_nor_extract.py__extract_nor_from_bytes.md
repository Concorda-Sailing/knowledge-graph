---
node_id: concorda-api::services/nor_extract.py::extract_nor_from_bytes
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 459282e9a346e632ebfbe6985511f9f3b5009a6baff5185f67e92a18362425a4
status: llm_drafted
---

# extract_nor_from_bytes

## Purpose

Performs automated extraction of Notice of Race (NOR) data from uploaded files using LLM-based parsing. It provides two entry points: `extract_nor_from_bytes` (which manages the database session) and `extract_nor_from_bytes_pure` (which accepts pre-fetched snapshots to avoid holding a DB connection open during the long-running LLM round-trip). Use the `_pure` variant for any asynchronous or background processing to prevent connection-pool exhaustion.

## Invariants

- **Returns a dictionary** with the shape `{"status": "extracted"|"refused", "message": str, "extracted_data": dict | None, "extracted_items": list | None}`.
- **Requires a valid LLM configuration.** If `config.get("api_key")` is missing, it raises `NORExtractError`.
- **Uses vision-based fallback.** If `extract_text` returns `None`, the function automatically switches to `vision_completion` using the file bytes.
- **Spreadsheet handling is explicit.** For `.xlsx`, `.xls`, or `.csv` files, a specific system prompt is prepended to the text content to ensure the LLM treats every non-empty row as a distinct event.

## Gotchas

- **Connection-pool exhaustion.** Per commit `8b2e30a`, calling the non-pure version within long-running loops or high-concurrency-tasks can exhaust the DB connection pool. Always prefer `extract_nor_from_bytes_pure` in background tasks.
- **MIME type sensitivity.** Per commit `8c74a42`, the vision-based extraction relies on a correctly formatted base64 string and MIME type (e.g., `image/jpeg`) to ensure the LLM can parse the visual data correctly.
- **Spreadsheet row-merging.** The system prompt for spreadsheets is designed to prevent the LLM from deduplicating rows that share names but have different dates/locations.

## Cross-cutting concerns

- **Auth**: None (relies on internal LLM API key configuration).
- **Websocket**: none
- **Audit**: N/A
- **Rate limit**: none
- **Side effects**: None.

## External consumers

None known.
