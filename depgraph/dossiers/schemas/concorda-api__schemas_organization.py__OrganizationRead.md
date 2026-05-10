---
node_id: concorda-api::schemas/organization.py::OrganizationRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 51b8bd380c6c7accb3749937b5c34dae47990225cc96480e33933075d5af6b64
status: current
---

# OrganizationRead

## Purpose
Pydantic response schema for the `Organization` ORM model — yacht clubs, sailing associations, and similar orgs that participate in MBSA. Returned by every read path on `/api/organizations*`: list, get-by-id, create, update, and the `/delegates` aggregate (wrapped inside `_DelegatesEntry.club`). Carries the full org card: `name`, `abbreviation`, `org_type`, nested `address`/`services`/`social_media` blobs, `burgee_url`, `vhf_channel`, `region`, `steward_id`, `billing_contact_id`, `fleet_captain_id`, plus `reciprocity_with` and `parent_org_id`. `from_attributes = True` lets routers `return db_org` directly. The flat-and-permissive shape (everything `Optional` except `id`/`type`/`created`/`modified`/`name`/`org_type`) reflects that orgs are imported piecemeal from CSV and curated over time — most fields were unknown at creation.

## Invariants
- `id`, `type`, `created`, `modified`, `name`, `org_type` are always present; everything else is optional and may be `None` on partially-curated orgs.
- `address`, `services`, `social_media` are typed as `Optional[dict]` here even though `OrganizationCreate` uses typed sub-models (`Address`, `Services`, `SocialMedia`). The read shape intentionally passes through the SQLite JSON column verbatim — do not tighten to the typed sub-models without auditing every imported row.
- `vhf_channel` is `Optional[int]`. CSV importer (`/import/csv`) coerces only digit strings; non-numeric VHF strings (e.g. "72A") have historically been dropped on import — keep this in mind before promoting the field to required.
- `steward_id`, `billing_contact_id`, `fleet_captain_id` are foreign-key strings to `Person.id` but the schema does not embed the Person — `/delegates` does that join itself via `_DelegatePublic`.
- `from_attributes = True` must remain set; routers return SQLAlchemy instances directly.

## Gotchas
- `abbreviation` is a recent addition (commit `bbe1627`, "organization abbreviation column"). Older imports and seed rows may have `None`; UI must fall back to `name` when rendering compact forms.
- `address` is a free-form `dict` — historical imports populated mixed shapes (some have `street`, some only `city`/`state`). `export/csv` reads via `addr.get("street", "")` for safety; new consumers should do the same rather than dataclass-destructuring.
- `burgee_url` is whatever was stored — relative path, absolute URL, or `None`. Don't assume a CDN host.
- `reciprocity_with` is a list of org ids (strings), not embedded `OrganizationRead` objects — resolving names requires a second fetch. Don't accidentally introduce N+1 expansion server-side without a plan.
- `region` was added in commit `1118209` ("crew pools, event crew invites, org regions"); pre-2026 orgs may have `None`.
- Returned by GET endpoints that are **unauthenticated** (`list`, `get`, `delegates`). Anything added here is publicly readable to any portal visitor — do not add private fields (notes, internal contact preferences, financial state) without first gating the route.

## Cross-cutting concerns
- Auth asymmetry: `GET /api/organizations`, `GET /api/organizations/{id}`, and `GET /api/organizations/delegates` are unauthenticated; `POST`, `PUT`, `DELETE`, `/export/csv`, `/import/csv` require `org_admin`/`system_admin` plus per-org scope via `_require_org_admin_scope`. The schema is shared across both worlds — adding a field here exposes it on the public reads.
- No audit log on org reads; `PUT`/`DELETE` mutations are not currently audited either (potential gap — billing-contact swaps are a financial pivot per the router's own comment).
- No websocket invalidation; clients re-fetch on their own lifecycle.
- `_DelegatesEntry` wraps this schema; any breaking field change ripples into the delegates aggregate.
- CSV export only emits a subset of fields (`name`, `org_type`, address parts, `phone_number`, `website`, `contact_email`, `vhf_channel`) — adding a field here does not auto-propagate to the export.

## External consumers
None known outside `concorda-web` (and indirectly the Expo app via the web org list). No webhooks, no scheduled jobs read this endpoint. The `_DelegatesEntry` shape is consumed by the public clubs/delegates page, so the read schema is effectively part of a public-ish contract.

## Open questions
- Should `GET /api/organizations/{id}` require auth? The router's own scoping comment frames billing-contact mutation as a "financial pivot," yet `billing_contact_id` and `contact_email` are publicly readable today.
- Should `address`/`services`/`social_media` be tightened from `Optional[dict]` to the typed sub-models used by `OrganizationCreate`? Would need a data audit first to confirm no row has fields outside those shapes.
- `parent_org_id` is exposed but no endpoint currently traverses it — is the parent/child org hierarchy a planned feature or vestigial?
