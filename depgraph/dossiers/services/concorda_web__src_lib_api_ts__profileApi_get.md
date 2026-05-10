---
node_id: concorda-web::src/lib/api.ts::profileApi.get
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 65a838a7f06ab34d808e5e3672b45670d509bdeb2f353d5c08e9138e2b6b0d52
status: llm_drafted
---

# profileApi.get

## Purpose

Client-side mirror for "who am I" — fetches the authenticated user's full profile (Person row plus memberships, preferences, and identity fields) from `GET /api/profile`. The handler in `concorda-api/routers/profile.py:75-81` is a one-liner that returns `current_user.user` shaped through `ProfileRead`. Distinct from `authApi.me` (`GET /api/auth/me`): `auth/me` is a lightweight session-bootstrap response carrying `id/email/name/picture_url`, `memberships`, `permissions`, and `pending_policy_acceptances` — what the shell needs to gate routes. `profileApi.get` is the fuller record: it adds `phone_number`, `additional_email/phone`, `mailing_address`, `date_of_birth`, `join_date`, `preferences` (full nested object — directory, crewfinder, my_schedule_filters, setup_wizard_completed, etc.), `email_verified`, `shirt_size`/`shorts_*`, `member_category`, `club_affiliations`, `meta`, plus `picture_url`/`banner_url`. The 8 consumers each pick a narrow slice — `preferences.setup_wizard_completed` (members/page), `preferences.crewfinder.opt_in` (regattas), `preferences.my_schedule_filters` (schedule-tab), `picture_url` (sidebar-nav), `phone_number` for completion scoring (use-dashboard-badges, profile-completion), or the whole record for the editable profile form (profile-inline).

## Invariants

- Auth-required: `Depends(require_auth)`. Always returns the *caller's own* Person — there is no `?user_id=` parameter and there shouldn't be (other-user reads go through directory/crewfinder).
- Response shape is `ProfileRead` (`schemas/profile.py:28`); the TS `Profile` interface (`api.ts:2077`) must stay in sync.
- `preferences` always comes back populated — `ProfileRead.fill_preference_defaults` merges over `DEFAULT_PREFERENCES` so consumers can read `p.preferences.crewfinder.opt_in` without a null guard on the section, but specific keys (e.g. `setup_wizard_completed`, `my_schedule_filters`) may still be undefined.
- `memberships` is an array of `MembershipInfo` (id/product_id/name/slug) hydrated by `convert_memberships` from the `PersonProduct` junction; never the raw ORM rows.
- `email_verified` is always present and boolean.

## Gotchas

- **Two endpoints, easily confused.** `authApi.me` and `profileApi.get` overlap on identity fields but differ on `permissions`/`pending_policy_acceptances` (auth/me only) vs the full preferences/address/sizing payload (profile only). Don't add permission checks based on `profileApi.get` — it doesn't carry them. Don't add preference reads to `auth/me` — it's intentionally lightweight.
- **Client `Profile` interface drift.** TS includes `banner_url` (line 2086) but `ProfileRead` does not declare it; it slips through because Pydantic `from_attributes=True` reads the ORM attribute directly. Add it to `ProfileRead` if a future migration tightens schema validation.
- **Preference partial-update pattern.** `update_profile` (PUT) does a deep merge of `preferences` and `meta` — read-modify-write isn't required, send only the changed section. But the GET response always contains the *fully-merged* preferences, so a consumer that round-trips the whole `preferences` object back to PUT will silently re-write defaults as explicit values.
- **No caching layer.** Each consumer hits `/api/profile` independently on mount — the dashboard tree can fire 3-4 parallel calls (page.tsx, sidebar-nav, schedule-tab, use-dashboard-badges). Tolerable today, but if a consumer is added inside a render-loop it will hammer the endpoint.
- **PUT broadcasts `PERSON_UPDATED` and conditionally `DIRECTORY_CHANGED`** (profile.py:140-142); GET does not. If you switch a consumer to live-update via WS, subscribe to those events and re-fetch.

## Cross-cutting concerns

- **Auth:** `require_auth` — 401 if no session.
- **Rate limits:** none on the GET; the sibling `change_password` has its own in-memory limiter (see `feedback_rate_limiter_single_worker`).
- **WebSocket events:** GET emits nothing. The PUT counterpart emits `PERSON_UPDATED` (always) and `DIRECTORY_CHANGED` (when preferences change, because directory visibility lives in `preferences.directory`).
- **Side effects:** none on read.
- **PII:** response contains `mailing_address`, `date_of_birth`, `phone_number`, `additional_email/phone` — never log the body; never relay to a non-self consumer.

## External consumers

None known. No Expo iOS app integration yet (the app uses its own auth flow and hasn't wired this endpoint). No webhooks. No scheduled jobs read `/api/profile`.

## Open questions

- Should `banner_url` be declared on `ProfileRead` to match the TS interface and the picture_url sibling?
- Is the parallel-fetch pattern across dashboard tabs worth consolidating behind a shared context/SWR key? Current cost is small but grows linearly with new tabs.
