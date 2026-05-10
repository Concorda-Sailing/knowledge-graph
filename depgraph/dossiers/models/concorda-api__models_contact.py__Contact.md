---
node_id: concorda-api::models/contact.py::Contact
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 79a8734577401c39155ba89ece40dfe3fa6e3df82291875041339c8575a28a2d
status: llm_drafted
---

# Contact

## Purpose

Backend SQLAlchemy model for a person who plays an organizational role at MBSA — a steward, fleet captain, billing contact, RC chair, PRO, regatta coordinator, etc. Each row holds the contact-card data (`name`, `email`, `phone`, `title`) plus an optional `person_uuid` link back to a real User. The model is intentionally decoupled from any one entity: a Contact is joined to organizations / regattas / series / events through `ContactRole` rows, so the same person can hold many roles across many entities without duplication. As of 2026-05-10, only the three org-contacts CRUD routes in `routers/organizations.py` consume it.

## Invariants
- `name` is the only required field. `email`, `phone`, `title`, `person_uuid` are all nullable — many contacts are bare name+title (e.g. "Fleet Captain TBD") with no contactable channel yet.
- `person_uuid` is a soft pointer to a `User.id`. There is no FK; a Contact may reference a User that never gets created, and a User deletion will not clean up the link.
- `BaseModel` injects `id`, `created`, `modified`, and the `type='Contact'` discriminator (set explicitly by `__init__` so polymorphic queries resolve).
- One Contact is meant to be reused across multiple `ContactRole` rows. Do not create a fresh Contact per role — that's what ContactRole was introduced to avoid.
- `title` here is a free-text label on the contact card (e.g. "Treasurer at HYC"); it is **not** the same as `ContactRole.role`, which is the structured role-on-entity. They can disagree.

## Gotchas
- Introduced in commit `d77f83f` alongside Series / RegattaDocument / RegattaIntent. The pairing with `ContactRole` came later in `a61b325`, which consolidated four separate junction tables into one. Anything older than 2026-04-01 referring to `organization_contacts` / `regatta_contacts` / `event_contacts` / `series_contacts` is stale — see the ContactRole dossier.
- `DELETE /organizations/{id}/contacts/{role_id}` deletes only the `ContactRole`, never the Contact. This is intentional: Contacts are reusable, and the orphan-after-last-role case is accepted today. Don't "fix" this without a design discussion.
- `email` is unvalidated and non-unique — two Contact rows with the same email are legal and exist in practice (separate billing vs. RC roles for the same person at different orgs).
- `person_uuid` being nullable means UI lookups must tolerate missing-User gracefully; don't assume joining to `users` succeeds.

## Cross-cutting concerns
- The three dependent routes are guarded by `_require_admin` + `_require_org_admin_scope(org_id, current_user)` — only org admins of the matching org can read/create/update. The model itself has no row-level auth.
- `POST /organizations/{id}/contacts` writes both a `Contact` and a `ContactRole` in one transaction; partial-failure means neither lands.
- No websocket events, no audit log, no notification side effects. If billing/treasurer changes ever need a paper trail, this is the layer to add it.
- PII surface: email + phone are PII. No special encryption at rest today; redaction lives at the router-serialization layer, not the model.

## External consumers
None known. The web admin UI is the only consumer of the org-contacts routes. No Expo app surfaces, no scheduled jobs, no webhooks. Treasurer / fleet captain / RC chair data is admin-only at present.

## Open questions
- Should `person_uuid` become a real FK to `users.id` (with `ON DELETE SET NULL`) now that the User model is stable? Today's soft pointer is a footgun waiting for a "delete user" flow.
- Is the `title` field pulling its weight given that `ContactRole.role` is the structured field? Risk of drift — two sources of truth for "what does this person do."
- When the last `ContactRole` for a Contact is deleted, should the Contact be auto-removed or kept as a reusable "address-book" entry? Today it's kept; that decision hasn't been explicitly ratified.
