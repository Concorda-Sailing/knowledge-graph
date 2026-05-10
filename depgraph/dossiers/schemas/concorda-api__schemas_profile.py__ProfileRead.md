---
node_id: concorda-api::schemas/profile.py::ProfileRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2164a8e32bdfef6c81eecab04a5144848372827addedd5e452c306fa9297e44d
status: llm_drafted
---

# ProfileRead

## Purpose

Backend Pydantic read schema for the user's own profile — the response shape of `GET /api/profile` and the return type of every "modify-then-return-self" endpoint in `routers/profile.py` (PUT profile, picture/banner upload+delete, membership upgrade). It serializes a `Person` ORM row (`from_attributes=True`) with two custom validators: `fill_preference_defaults` deep-merges the stored `preferences` JSON over `DEFAULT_PREFERENCES` so consumers can read `p.preferences.crewfinder.opt_in` without null guards, and `convert_memberships` flattens the `PersonProduct` junction into `MembershipInfo` (id/product_id/name/slug). It is the *fuller* identity payload — distinct from the lightweight `auth/me` (permissions, pending policies, no preferences/address/sizing) — and is the contract the TS `Profile` interface in `concorda-web/src/lib/api.ts` mirrors. Fans to 7 dependents, all in `routers/profile.py`.

## Invariants

- `from_attributes = True` — serializes directly off the `Person` ORM row. Any attribute the schema names must exist on `Person` (or on a relationship resolver) at read time.
- `preferences` is *always* populated in the response. `fill_preference_defaults` substitutes `DEFAULT_PREFERENCES` when the DB column is null/empty, and otherwise merges section-by-section over defaults. Consumers may rely on top-level sections (`directory`, `crewfinder`, `mailing_list`) being present; individual keys inside a section may still be absent.
- `memberships` is a list of dicts shaped `{id, product_id, name, slug}` — never raw `PersonProduct` ORM rows. `convert_memberships` runs `mode="before"` and pulls `product.name`/`product.slug` via the relationship; an N+1 is possible if `PersonProduct.product` isn't eager-loaded.
- `mailing_address` is typed as `Optional[dict]` — *not* the `Address` Pydantic model, even though `ProfileUpdate` uses `Address`. Reads pass the raw JSON dict through; writes go through `Address.model_dump()` in the PUT handler.
- `email_verified: bool` is required (no default). A `Person` with this column null will fail validation — should not happen in practice but worth knowing for fixture-builders.
- TS `Profile` interface (`api.ts:2077`) must stay aligned. Note: TS includes `banner_url` but `ProfileRead` does not declare it — it slips through because of `from_attributes=True`.

## Gotchas

- **Preference defaults bit us once and shaped this validator.** Commit `03a6819` ("Fix preferences null crash: fill defaults in ProfileRead validator") added `fill_preference_defaults` after a null `preferences` column crashed serialization for users created before the preferences feature shipped. Don't remove the `if not v or not isinstance(v, dict)` short-circuit.
- **Round-trip footgun.** Because GET returns *fully-merged* preferences, a consumer that reads the whole `preferences` object, mutates one key, and PUTs the whole thing back will silently re-write every default as an explicit DB value. The 7 web consumers all send only the changed sub-section — preserve that pattern. (See `profileApi.update` dossier.)
- **`banner_url` schema drift.** TS declares it; Python schema does not. Works today because of `from_attributes`, but a future Pydantic strict-mode flip would silently drop the field from responses.
- **`mailing_address` asymmetry.** Read shape is `dict`; write shape is `Address` (typed). If you tighten the read type to `Address`, every legacy row with a flat-string mailing_address (per Person model dossier — schema evolved over time) will fail validation.
- **`convert_memberships` is `mode="before"`** and runs against ORM objects; if a future change pre-converts `PersonProduct` to dicts elsewhere, the `hasattr(item, "product")` branch is bypassed and the `id/product_id/name/slug` shape may regress.

## Cross-cutting concerns

- **Auth:** indirectly — every endpoint that returns `ProfileRead` is `Depends(require_auth)`. The schema itself contains PII (`mailing_address`, `date_of_birth`, `phone_number`, `additional_email/phone`); never log a serialized response, never relay to a non-self consumer.
- **WebSocket events:** the schema has no events of its own, but the PUT handler that returns it broadcasts `PERSON_UPDATED` always and `DIRECTORY_CHANGED` when `preferences` is in the payload (because directory visibility lives in `preferences.directory`).
- **Side effects:** none on serialization. Validators are pure.
- **Privacy gate:** per `feedback_crew_visibility_privacy`, peer crew identities are hidden unless their resume is published — `ProfileRead` is *self-only*, so this gate doesn't apply here, but copying the shape into a peer-visible endpoint would leak PII.

## External consumers

None known directly. The Concorda iOS app has its own auth flow and does not yet call `/api/profile`. No webhooks, no scheduled jobs. Indirectly, every dashboard/profile/setup UI in `concorda-web` consumes this shape via `profileApi.get` / `profileApi.update`.

## Open questions

- Should `banner_url` be declared on `ProfileRead` to match the TS interface and the `picture_url` sibling? (Carried over from `profileApi.get`.)
- Should `mailing_address` move from `Optional[dict]` to the typed `Address` model, with a one-time migration to coerce legacy flat-string rows? Currently the read-vs-write asymmetry is a hidden trap.
- The validator imports inside `fill_preference_defaults` (`DirectoryPrefs`, `CrewfinderPrefs`, `MailingListPrefs`) are unused. Dead code or vestige of a planned typed-merge? Worth deleting or completing.
