---
node_id: concorda-api::models/person.py::Person
node_kind: model
feature: identity
last_reviewed: 2026-05-09
last_reviewed_against_hash: 2ddcb6a8a44e68894924895d86fefef52992e788ccc7da8a41ab6efea14c2b60
status: current
---

# Person

## Purpose

The root identity record. Every authenticated actor in the system — members, admins, agents acting on behalf of an org, anyone who has ever been invited or signed up — exists as a `Person` row. The model is intentionally broad: it carries identity (name, email, password hash), profile metadata (mailing address, shirt size, club affiliations), preferences, oauth linkage, calendar token for ICS feeds, and a set of `additional_data` JSON for fields that don't merit their own column.

`email` is unique across the whole table — we do not allow multiple Persons with the same email even across different organizations. This is load-bearing for invite-claim flows, oauth login, and the email-verification gate.

## Invariants

- **`email` is unique and case-folded at compare time.** The column is plain `String(255)` but every comparison route in the codebase normalizes via `_normalize_email` (Unicode NFC + strip + lowercase) before matching. Storing two Persons with `Bob@x.com` and `bob@x.com` is forbidden because real users won't be able to log in deterministically.
- **`password_hash` may be null.** Oauth-only and invited-but-not-yet-registered Persons exist. Auth code must always check `hash is not None` before bcrypt-comparing — never assume.
- **`email_verified` gates free signups.** Per memory `project_free_signup_verification`, anti-bot logic refuses login for unverified free signups. Don't add a code path that auto-verifies without going through the existing email-token flow.
- **`tos_accepted_at` is the policy-acceptance proof.** Login redirects to `/policies/accept` until this is set. Migrations that add a new policy version reset this.
- **`organization_ids` is legacy.** Real org membership lives in the `person_organizations` junction table via the `organizations` relationship. The JSON column persists for SQLite-compat data lineage; do not write new code that reads or writes it.
- **`disabled_permissions` is a deny-list.** It overrides positive grants in `UserRole`. An admin who is in `disabled_permissions: ["admin.delete_user"]` cannot delete users even with the role — checked in the permission resolver, not at the row level.
- **`calendar_token` is unique and indexed.** Used in unauthenticated ICS feed URLs. Rotating it invalidates every subscribed calendar app immediately.

## Gotchas

- **`__init__` injects `type="Person"`.** This is for SQLAlchemy single-table inheritance with the legacy `BaseModel.type` discriminator. If you instantiate `Person()` directly elsewhere, `type` is set automatically — but if you bypass the constructor, the row will fail constraints.
- **Many JSON columns have evolved schemas over time.** `mailing_address` started as a flat string, became a dict. `preferences` accumulates keys without migration. Reading these fields needs `.get()` defaults, not bracket access.
- **Several `# Legacy columns` are still hot.** `picture_url`, `join_date`, `member_category` etc are documented as "kept for SQLite compat" but production code still reads/writes them. Don't drop them without a coordinated migration + frontend sweep.
- **70 endpoints query Person directly.** Any change to required-vs-nullable, type widening, or column rename breaks more than you can scan by eye. Use the depgraph dependents list before refactoring.

## Cross-cutting concerns

- **Auth:** `password_hash` (bcrypt), `oauth_provider` + `oauth_id` (Google), `email_verified` flag, `tos_accepted_at` policy gate. All of these gate login.
- **Calendar:** `calendar_token` powers public ICS feeds.
- **Permissions:** `UserRole` rows reference `person_id`. `disabled_permissions` is a per-row override.
- **Memberships:** `PersonProduct` rows track membership tier and expiry.
- **Privacy:** Per memory `feedback_crew_visibility_privacy`, peer crew identities are hidden unless the resume is published. Person fields read by crewfinder/boatfinder must respect this gate.

## External consumers

- **Concorda iOS app**: every screen that loads a profile reads Person fields. Adding a non-nullable column without a default will break old TestFlight/AppStore builds at deserialization time.
- **Stripe metadata:** `stripe_customer_id` (in `additional_data`) tracks the linked Customer. Don't rename.
- **ICS subscribers:** Apple Calendar / Google Calendar clients that subscribed via `calendar_token` continue to fetch even after the user logs out.

## Open questions

- The split between dedicated columns and `additional_data` JSON has drifted. A future cleanup could migrate `shirt_size`, `shorts_waist`, `shorts_inseam`, `member_category` into a typed `MerchPreferences` JSON sub-document.
- `organization_ids` legacy column should eventually be deleted; needs confirmation that nothing reads it.
