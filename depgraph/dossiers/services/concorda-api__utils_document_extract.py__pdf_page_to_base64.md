---
node_id: concorda-api::utils/document_extract.py::pdf_page_to_base64
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: c3e54ce02d1c89b91512eba36133dc412d0380bbfcc08c2106a0d22cdbdf0222
status: current
---

# pdf_page_to_base64

## Purpose

Converts a specific page of a PDF into a base64-encoded PNG string. This is used to prepare visual data for vision-model consumption (e.g., OCR or visual analysis). It is distinct from the CSV/text extraction helpers in the same file, which return raw text/strings; this function specifically produces a data URI for image-based processing.

## Invariants

- **Input is `bytes`** — expects the raw file content of a PDF.
- **Returns a Data URI** — the output is a string prefixed with `data:image/png;base64,`.
- **`page_num` is zero-indexed** — follows standard `fitz` (PyMuPDF) indexing.
- **`dpi` controls scaling** — the `matrix` calculation `dpi / 72` determines the resolution of the resulting PNG.

## Gotchas

- **Relocated via `ef1c3bd`** — this helper was moved from a root-level location into `utils/` during the recent refactor. Ensure any imports targeting this function are updated to the new path.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: N
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
