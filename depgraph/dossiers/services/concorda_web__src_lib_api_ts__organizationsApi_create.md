---
node_id: concorda-web::src/lib/api.ts::organizationsApi.create
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 0dcf29c4c64a9e673dead5e09a49bb68314cc5d092d45b72b8337029a5ab097f
status: llm_drafted
---

# organizationsApi.create

## Purpose

Creates a new organization record via the backend API. It is a specialized part of the `organizationsApi` object, distinct from `update` or `delete` which require an existing `id`. An agent should use this method when implementing workflows that involve onboarding new entities into the system.

## Invariants

- **HTTP Method is `POST`** — calls the `/api/organizations` endpoint.
- **Requires `OrganizationCreate` payload** — the input must match the expected shape for a new organization.
- **Uses `fetchApiAuthenticated`** — requires a valid bearer token to succeed.
- **Returns a single `Organization` object** — the response shape is the fully hydrated organization record.

## Gotchas

- **Authentication requirement** — because it uses `fetchApiAuthenticated`, any call to this method will fail if the user's session has expired or if the token is missing.
- **Dependency on `ClubDialog`** — the `ClubDialog` component (specifically at `club-dialog.tsx:158`) relies on this method for its creation flow; changes to the input shape will break the admin UI.

## Cross-cutting concerns

- **Auth**: Uses `fetchApiAuthenticated` (requires bearer token).
- **Side effects**: Creation of an organization is a foundational event that likely triggers downstream effects in the admin dashboard and organization-specific views.

## External consumers

- `concorda-web::src/components/admin/club-dialog.tsx::ClubDialog`
