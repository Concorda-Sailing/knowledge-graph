---
node_id: concorda-api::utils/document_extract.py::extract_text
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8c2a236f00c047e51e7e894c3f22e41a8f0c748c0584f610872bc741a529e602
status: llm_drafted
---

# extract_text

## Purpose

The primary text extraction engine for the Concorda API. It converts raw file bytes from various formats (PDF, DOCX, XLSX, CSV, HTML, and plain text) into a single string of text. This function acts as the bridge between raw file uploads and downstream LLM processing; if it returns `None`, the system is intended to fall back to a vision-based extraction model.

## Invariants

- **Input is raw bytes.** The function expects `file_bytes: bytes` and a `filename: str` to determine the parsing logic.
- **Returns `str` or `None`.** A successful extraction returns a string; an unsupported format or a file with no text layer (e.g., a scanned PDF) returns `None`.
- **Uses `errors="replace"` for decoding.** Text-based formats (TXT, HTML, CSV) use the "replace" strategy to prevent `UnicodeDecodeError` from crashing the service.
- **PDFs use page delimiters.** Extracted PDF text is joined using the explicit delimiter `"\n\n--- Page Break ---\n\n"` to preserve structural context for the LLM.

## Gotchas

- **Vision fallback trigger.** Per the logic in `extract_text`, returning `None` for image extensions (`.jpg`, `.png`, etc.) is an intentional signal to the caller to use a vision model rather than a failure state.
- **Scanned PDF-only mode.** If a PDF contains no text layer (e.g., a scanned image of a document), `_extract_pdf` returns `None`, which will trigger the vision-based processing path in the caller.
- **Relocated via refactor.** Per commit `ef1c3bd`, this utility was recently moved from the root level to `utils/`. Ensure any new imports or tests point to this new location.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: None known.

## External consumers

None known.
