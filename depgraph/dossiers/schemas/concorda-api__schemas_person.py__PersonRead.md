---
node_id: concorda-api::schemas/person.py::PersonRead
node_kind: schema
feature: identity
last_reviewed: 2026-05-09
last_reviewed_against_hash: 17b12c1e376df91414bd95554d12429f257416af3eb173213d20beb3ff410edb
status: current
---

# PersonRead

## Purpose

The wire format for a Person record going *out* of the API. Every endpoint that returns a person — `/api/auth/me`, `/api/persons`, `/api/persons/{id}`, `/api/admin/users/...`, `/api/profile`, `/api/admin/members` — uses this shape (or a derivative).

## Invariants

- **`id`, `type`, `created`, `modified`** come from `BaseModel` and are always present. Do not remove these from the response — every consumer that caches a Person assumes they're there.
- **`memberships: list[MembershipInfo]`** is computed by the `convert_memberships` field validator. Inputs that come in as raw `PersonProduct` rows are normalized into the structured `MembershipInfo` shape. Don't rely on the input shape; the validator is the canonical translator.
- **`email_verified` is required.** It's used everywhere in web to gate features. Defaulting to `True` if missing would silently break the anti-bot gate (memory `project_free_signup_verification`).
- **All other fields are optional.** Production data has many Persons with sparse profile fields; consumers must handle null/missing gracefully.
- **Legacy fields are exposed as-is**: `picture_url`, `join_date`, `leave_date`, `member_category`, `shirt_size`, etc. They live in the model under `# Legacy columns` but the Pydantic shape doesn't distinguish — clients see one flat object.

## Gotchas

- **`organization_ids: Optional[list[str]]`** — the Person model's `organization_ids` is a JSON column kept for migration lineage. Reading it directly from a PersonRead is fine for legacy clients, but real org membership lives in the `organizations` relationship. Future: deprecate this field in PersonRead in favor of a sibling `organizations: list[OrganizationSummary]`.
- **`memberships: list[MembershipInfo] = []`** has a default of empty list — but `Preferences()` for `preferences` does not, requiring instantiation. Consistency would help; today it's just a quirk.
- **The Pydantic v2 `field_validator` runs `mode="before"`** — so it sees raw input, not Pydantic-validated data. If you change the upstream representation of `memberships`, this validator is the place to update first.

## Cross-cutting concerns

- **iOS app**: every Person-displaying screen deserializes this. A non-nullable field added without a default will break shipped builds at deserialization time. Consider that for any new field.
- **Web type generation**: the TypeScript `AuthUser` and similar types in `concorda-web/src/lib/api.ts` should stay in sync with PersonRead. Today they're hand-maintained; consider auto-generation from the OpenAPI schema.
- **Admin dashboards** display fields that other surfaces don't (e.g., `disabled_permissions`). Those use a separate `AdminPersonRead` shape; keep this PersonRead lean.

## External consumers

- 7 endpoints surface a PersonRead (or a subclass). Editing a field on PersonRead typically requires:
  1. Update the model column (or the `additional_data` JSON access).
  2. Update PersonRead here.
  3. Update web's TypeScript types (`AuthUser`, `Person`, etc.).
  4. Update Expo's deserializer.
  5. Update test fixtures in `concorda-test/lib/test-data.ts`.

## Open questions

- Should PersonRead split into `PersonReadLite` (id/name/email) and `PersonReadFull` (all the merch/profile fields)? Many list endpoints carry the full shape unnecessarily.
