---
node_id: concorda-api::models/regatta_document.py::RegattaDocument
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 4c8ed55fdf613aa5893002f8d0a429cb10ed5a455414ac38508fbdfd4527c3ff
status: current
---

# RegattaDocument

## Purpose

The database model for documents associated with a specific regatta (e.g., NOR, Sailing Instructions, or Flyers). It serves as the metadata container for files hosted externally, tracking both the file's location and the state of its automated data extraction. Use this model when you need to link a file URL to a `regatta_uuid` or track the progress of the `extraction_status` pipeline.

## Invariants

- **`regatta_uuid` is the primary lookup key.** It is a non-nullable 36-character string used to group documents within a specific regatta context.
- **`document_type` is restricted to a specific set of strings.** Valid values are `nor`, `sailing_instructions`, `flyer`, `results`, or `other`.
- **`file_url` must be a full URI.** It is a non-nullable string up to 500 characters.
- **`extraction_status` tracks the processing pipeline.** It tracks the lifecycle of a document through `pending`, `extracted`, `reviewed`, or `failed`.
- **`extracted_data` is a JSON blob.** It stores the structured results of the document parsing process.

## Gotchas

- **`regatta_uuid` is not a foreign key to a `Regatta` table.** It is a raw string index. Ensure the UUID exists in the parent context to avoid orphaned documents.
- **`extraction_status` is nullable.** Per the model definition, `extraction_status` and `extracted_data` can be null, which may cause issues if the downstream extraction engine expects a strict state machine.

## Cross-cutting concerns

- **Auth**: Requires `RegattaDocument` ownership or organization-level permissions to view/edit.
- **Audit**: N/A.
- **Side effects**: The `extraction_status` field triggers the background extraction worker (see extraction pipeline documentation).

## External consumers

None known.
