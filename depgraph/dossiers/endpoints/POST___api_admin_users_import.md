---
node_id: POST::/api/admin/users/import
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2b52c004a1591181ec0a4dddbc9e5d8e8aec62e77a91e41ac122c5f875f43efc
status: llm_drafted
---

# POST /api/admin/users/import

## Purpose

Bulk-imports users from a CSV file into the system. It supports two modes via the `on_duplicate` query parameter: `skip` (ignores existing users) or `update` (overwrites existing user data). This is the primary mechanism for onboarding large rosters or syncing external member lists.

## Invariants

- **Method/Path**: `POST /api/admin/users/import`.
- **File Format**: Must be a `.csv` file; the function explicitly checks the file extension and raises a 400 error if it is not.
- **Required Columns**: The CSV must contain `first_name`, `last_name`, and `email`.
- **Auth**: Requires a valid authenticated session via `require_auth`.
- **Data Normalization**: Headers are automatically stripped of whitespace and lowercased to prevent mapping errors.
- **Email Validation**: Uses `EMAIL_RE` to validate the email format; invalid emails result in a row-level error rather than a total process failure.

## Gotchas

- **Privilege Escalation Protection**: In `update` mode, the function calls `_require_can_modify_user`. If an attempt is made to update a user with higher privileges, the row is skipped and an error is logged. This was a critical fix to prevent admins from accidentally or maliciously demoting higher-level users (see commit `650233f`).
- **Header Sensitivity**: While the function normalizes headers (lowercase/strip), the `required` set is strictly enforced. If the CSV lacks the exact required columns after normalization, the entire request fails.
- **Encoding**: The function uses `utf-8-sig` to decode the file, which handles the Byte Order Mark (BOM) often found in Excel-generated CSVs.

## Cross-cutting concerns

- **Auth**: Depends on `require_auth` to ensure only authorized administrators can trigger imports.
- **Audit**: While the endpoint itself doesn't explicitly call an audit logger, it relies on the `_require_can_modify_user` guard which is part of the security boundary for user-modifying endpoints.
- **Side effects**: Successful imports/updates will change the `Person` records, which may affect any UI components displaying user details or membership status.

## External consumers

- `concorda-web::src/lib/api.ts::adminApi.importUsers` (via `adminApi.importUsers`)
