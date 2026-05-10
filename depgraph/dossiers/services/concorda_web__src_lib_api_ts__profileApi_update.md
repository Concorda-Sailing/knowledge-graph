---
node_id: concorda-web::src/lib/api.ts::profileApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6e6873772013b442fc77669c004fed25d6e5b6512da44f2dc6edb4af60dadcc6
status: llm_drafted
---

# profileApi.update

## Purpose

Client-side mirror for the user's own profile PUT — wraps `PUT /api/profile` and returns the refreshed `Profile`. The handler in `concorda-api/routers/profile.py:84-143` is a *partial update*: it does `model_dump(exclude_unset=True)` and only writes fields the caller actually sent. `preferences` and `meta` are deep-merged against the existing JSON columns (preferences merges section-by-section, meta does a flat top-level update), so callers can — and should — send only the changed sub-object. After commit it broadcasts `PERSON_UPDATED` always, plus `DIRECTORY_CHANGED` if `preferences` was in the payload (because directory visibility lives in `preferences.directory`). The 7 consumers each carry a narrow write: `privacy-form` flips `preferences.directory.*`, `crewfinder-publish-bar`/`crewfinder-visibility` toggle `preferences.crewfinder.opt_in`, `directory-publish-bar` toggles `preferences.directory.opt_in`, `regattas`/`setup` page complete the setup wizard via `preferences.setup_wizard_completed`, and `schedule-tab` persists `preferences.my_schedule_filters`.

## Invariants

- Auth-required (`Depends(require_auth)`); always writes to the caller's own Person — no `user_id` parameter.
- Allowlist on the backend (`PROFILE_ALLOWED_FIELDS`, profile.py:127-133) — anything outside that set is silently dropped. If you add a column to `Person`, add it to both `ProfileUpdate` and the allowlist or PUTs become no-ops.
- `preferences` and `meta` are *merged*, not replaced. A PUT with `{preferences: {crewfinder: {opt_in: true}}}` leaves `preferences.directory` and `preferences.my_schedule_filters` untouched.
- `mailing_address` is a nested Pydantic model that gets `.model_dump()`'d before assignment — it *replaces* wholesale (no merge), unlike preferences.
- TS `ProfileUpdate` interface (search `api.ts` for `interface ProfileUpdate`) must stay aligned with `schemas/profile.py::ProfileUpdate`.
- Response is the freshly-refreshed `Profile` — callers can trust `setProfile(await profileApi.update(...))` without a follow-up GET.

## Gotchas

- **Round-tripping the whole `preferences` object turns defaults into explicit values.** `profileApi.get` returns *fully-merged* preferences (defaults filled in by `fill_preference_defaults`); if a consumer reads that, mutates one field, and PUTs the whole object back, it writes every default key as an explicit DB value. Always send only the changed section. The 7 current consumers all do this correctly — preserve the pattern.
- **Section-level merge is shallow per section.** `preferences.directory.opt_in` and `preferences.directory.show_phone` sent in separate PUTs both stick because the merge does `existing_prefs[section].update(values)`. But sending `preferences: {directory: {opt_in: true}}` will *not* clear sibling keys inside `directory`. There is no way to "unset" a single preference key via this endpoint short of sending an explicit `null` and having the schema accept it (it currently strips `None` via `exclude_none=True` on line 106).
- **`meta` merge is flat (top-level only).** Unlike `preferences`, `meta` uses `existing_meta.update(new_meta)` — nested dicts in `meta` will be replaced, not deep-merged. If a consumer ever stores nested meta, this will surprise them.
- **`DIRECTORY_CHANGED` fires whenever `preferences` is in the payload**, even if the changed section is `my_schedule_filters` (purely client-side state). That's an over-broadcast — directory subscribers re-fetch on every schedule-filter change. Not currently painful, but worth knowing if directory live-updates get expensive.
- **Recent commits have not touched `update_profile`** — the file's churn is all in events/crew/co-owner/regatta paths. The PUT handler is stable; treat changes here with extra care.

## Cross-cutting concerns

- **Auth:** `require_auth` — 401 if unauthenticated.
- **Rate limits:** none on this endpoint. (Sibling `change_password` has its own in-memory limiter; see `feedback_rate_limiter_single_worker`.)
- **WebSocket events:** `PERSON_UPDATED` (always), `DIRECTORY_CHANGED` (when payload includes `preferences`). Subscribers in directory/crewfinder/dashboard rely on these to invalidate caches.
- **Side effects:** single `db.commit()` then `db.refresh(user)`; no downstream model writes, no email, no audit row.
- **PII:** payload may carry `phone_number`, `additional_email/phone`, `mailing_address`, `date_of_birth` — don't log request bodies.

## External consumers

None known. Expo iOS app does not call this endpoint yet. No webhooks, no scheduled jobs.

## Open questions

- Should `DIRECTORY_CHANGED` only fire when `preferences.directory` specifically changed, rather than on any preferences write?
- Should the endpoint support a `null`-as-clear semantic for individual preference keys, or is the current "merge-only, never delete" semantic intentional?
