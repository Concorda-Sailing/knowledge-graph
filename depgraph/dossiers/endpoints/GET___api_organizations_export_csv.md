---
node_id: GET::/api/organizations/export/csv
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2433dd3e3d71b852605733b725e1c7463b3873652a31cd42f3e5abd03e3ccaea
status: current
---

# GET /api/organizations/export/csv

## Purpose

Generates a downloadable CSV containing a full list of all organizations in the database. It is used primarily for administrative backups or data portability. Unlike the `/import/csv` endpoint which handles stateful creation, this is a read-only export that returns a `StreamingResponse` of the current organization registry.

## Invariants

- **HTTP Method is `GET`**.
- **Requires `admin.clubs.export` permission** via the `require_permission` dependency.
- **Returns a `text/csv` media type** with a `Content-Disposition` header set to `attachment; filename=organizations.csv`.
- **Order is deterministic** based on `Organization.name`.
- **Address data is nested**; the exporter flattens the `address` dictionary into individual columns (`street`, `city`, `state`, `zip`) for the CSV output.

## Gotchas

- **The export is a single-pass stream.** The current implementation uses `iter([output.getvalue()])`, which means the entire CSV is generated in memory before being streamed. For extremely large organization lists, this could lead to memory pressure.
- **Address field flattening.** If the `address` field is missing or malformed, the code uses `org.address or {}` and `.get()` to prevent attribute errors, ensuring the export doesn't crash on incomplete data.

## Cross-cutting concerns

- **Auth**: Requires `admin.clubs.export` permission.
- **Audit**: N/A.
- **Rate limit**: None explicitly defined, but subject to general API rate limiting.
- **Side effects**: None.

## External consumers

- `concorda-web::src/lib/api.ts::organizationsApi.exportCsv` (Internal web client).
