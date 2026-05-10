---
node_id: concorda-api::services/nor_extract.py::extract_nor_from_bytes_pure
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 87061c6214adb2743a7ba54df74dd18d7bd8ea83001e059a9b0a6d1da53eb638
status: llm_drafted
---

# extract_nor_from_bytes_pure

## Purpose

Performs the core logic for extracting Notice of Race (NOR) data from raw bytes using an LLM. It is the "pure" version of the extraction service, designed to be called after a database session has been closed to avoid connection-pool exhaustion. It handles the branching logic between text-based extraction and vision-based extraction (for PDFs or images) and applies specific prompting instructions for tabular spreadsheet data.

## Invariants

- **Input is pre-fetched.** The caller must provide a `_PromptSnapshot` and a `config` dict, typically obtained via `load_extract_prereqs`.
- **Returns a dictionary.** The return shape is `dict[str, Any]`, containing the extracted data or a "refused" status.
- **Text length limits.** If `text_content` is under 50 characters, it returns a "refused" status immediately. If over 30,000 characters, the content is truncated to prevent LLM context overflow.
- **Vision fallback.** If `extract_text` returns `None`, the function automatically switches to a vision-based approach using `vision_completion`.

## Gotchas

- **MIME type preservation.** Per commit `8c74a42`, the function must ensure the `file_mime` is correctly passed or defaulted (e.g., to `image/jpeg`) to ensure `vision_completion` receives a valid base64 data URI.
- **Spreadsheet row handling.** For `.xlsx`, `.xls`, or `.csv` files, a specific instruction is injected into the prompt to prevent the LLM from merging rows that share the same event name but differ in date or location.
- **Connection-pool exhaustion.** This pure function exists specifically to solve the issue where long-running LLM calls held open a DB connection. Use this instead of the non-pure version when calling from a context where the DB session should be closed (see commit `8b2e30a`).

## Cross-cutting concerns

- **Auth**: None (expects pre-authenticated/pre-fetched data).
- **Websocket**: None.
- **Audit**: N/A.
- **Rate limit**: None.
- **Side effects**: Directly affects the success of the `POST /api/nor/extract/{0}` endpoint.

## External consumers

- `POST /api/nor/extract/{0}` (via `routers/nor.py`).
