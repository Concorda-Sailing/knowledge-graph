---
node_id: GET::/api/organizations
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ff427e360b32dca3c5f87e80a5078a366caa1eb0f500737d9b58919dde53adb7
status: llm_drafted
---

# GET /api/organizations

## Purpose

Fetches a list of all organizations (clubs, sailing centers, etc.) in the system. It supports filtering by `org_type` via a query parameter and returns the results ordered alphabetically by name. This is the primary endpoint for populating directory-style views and dropdowns in the web and mobile apps.

## Invariants

- **Returns a list of `OrganizationRead` objects.** The response is a JSON array of objects containing the organization's core identity and metadata.
- **Ordering is strictly alphabetical.** Results are returned via `order_by(Organization.name)`, ensuring consistent UI presentation.
- **`org_type` is an optional filter.** If provided, the query is restricted to that specific type (e.g., "Yacht Club" or "Sailing Center").
- **Address data is nested.** The `address` field is a dictionary/JSON field within the organization record.

## Gotchas

- **Recent expansion of organization types.** Per commit `45f2bec`, the directory now includes "sailing centers" and "racing associations" in addition to standard yacht clubs; ensure any client-side type enums are updated to reflect this broader scope.
- **CSV Import/Export logic is distinct.** While this endpoint handles the GET request, the sibling `POST /import/csv` and `GET /export/csv` have much stricter permission requirements (`admin.clubs.import` and `admin.clubs.export`) than this base GET endpoint.

## Cross-cutting concerns

- **Auth**: None (Publicly accessible or relies on global middleware/session-based access depending on the router's parent configuration).
- **Rate limit**: none
- **Side effects**: Used to populate the organization selection lists in the "crew finder" and "directory" views.

## External consumers

None known.
