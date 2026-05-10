---
node_id: POST::/api/organizations/import/csv
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: b3169c0f1c1a4dc92d69dc734910c8d0817e79edb1b96e43bfb5d3bc28df06cb
status: current
---

# POST /api/organizations/import/csv

## Purpose

Provides a bulk ingestion mechanism for organization data via CSV upload. This is the primary tool for seeding the directory with sailing centers and racing associations. Use this instead of individual `POST /api/organizations` calls when initializing new environments or migrating legacy club data.

## Invariants

- **Requires `admin.clubs.import` permission** via the `require_permission` dependency.
- **Input must be a `.csv` file.** The function explicitly checks the filename extension and raises a 400 error if it does not end in `.csv`.
- **Uses UTF-8-SIG encoding.** The content is decoded using `utf-8-sig` to handle potential Byte Order Marks (BOM) from Excel-generated CSVs.
- **Skips existing organizations.** If a row contains a `name` that already exists in the `Organization` table, that row is skipped without erroring the entire batch.
- **Returns a summary object.** The response shape is `{ "imported": int, "skipped": int, "errors": list[str] }`.

## Gotchas

- **Implicit row skipping on name collision.** Because the function checks `Organization.name == name` before inserting, a duplicate name results in a `skipped` count rather than a failure. This can lead to silent failures if the user expects a strict import.
- **Strict integer conversion for VHF.** The `vhf_channel` field is parsed via `int(vhf) if vhf and vhf.isdigit()`. If a non-digit string is provided, it defaults to `None` rather than raising a validation error.
- **Address field stripping.** The address object is constructed by stripping whitespace from `street`, `city`, `state`, and `zip`. If a field is an empty string or whitespace, it is omitted from the resulting dictionary.

## Cross-cutting concerns

- **Auth**: Requires `admin.clubs.import` permission.
- **Audit**: N/A.
- **Side effects**: Successful imports populate the organization directory used by the crew finder and sailing center detail pages.

## External consumers

- `concorda-web::src/lib/api.ts::organizationsApi.importCsv`

## Open questions

- Should the import support a "force" flag to overwrite existing organizations with the same name, or is the current "skip-on-duplicate" behavior the desired safety mechanism?
