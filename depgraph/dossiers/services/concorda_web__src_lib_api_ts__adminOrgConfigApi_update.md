---
node_id: concorda-web::src/lib/api.ts::adminOrgConfigApi.update
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 8feff1eb48effd518e0981a94a2a021330ed365fc81f87b1c0dcbad4f0cb4f73
status: current
---

# adminOrgConfigApi.update

## Purpose

Admin-only client-side mirror for `PUT /api/admin/org-config` — the single mutation point for the `OrgConfig` singleton row that holds org branding (`org_name`, `app_title`, `logo_url` via siblings), `timezone`, `default_membership_id` for public signup links, and operational knobs (`register_rate_limit_*`, `error_notify_email`, `error_notify_cooldown_seconds`). Sends a `Partial<OrgConfigData>` so callers patch one section at a time. The values written here flow back to every client through `constantsApi.getAll` (see its dossier) — branding, document title, tz-aware formatters across ~30 components, and the default-membership selector on signup. If you're changing what an admin can configure about the org, this is the gate.

## Invariants

- System-admin gated. Backend `_require_system_admin(current_user)` rejects everyone else; the frontend doesn't enforce this — it relies on the page being routed under `/members/admin/system` and the API returning 403.
- `Partial<OrgConfigData>` semantics — backend uses `data.model_dump(exclude_unset=True)`, so omitted fields are left untouched. Three separate save buttons on the admin page call `update` with disjoint payloads (branding, rate-limit, alerts) and that's intentional; do not collapse them into one giant save.
- `error_notify_email: ""` (empty string) is the documented signal to **clear** the recipient and disable alerts — backend converts `""` → `None`. Don't "helpfully" omit empty strings client-side; you'd lose the disable path.
- `OrgConfig` is a singleton (`db.query(OrgConfig).first()`); the handler creates the row on first write if missing. There is exactly one row, ever.
- Response is the full updated `OrgConfigResponse` — callers `setConfig(updated)` to re-sync local form state, and the branding save explicitly calls `constantsManager.refresh()` afterwards so the rest of the app sees new values without a reload.

## Gotchas

- Stale constants cache: only the branding save (`page.tsx:78`) calls `constantsManager.refresh()`. The rate-limit and alerts saves don't — fine today because those fields aren't read through `useConstants()`, but if you add a new constants-exposed field to the alerts/rate-limit forms, you must also refresh, or other tabs/components will keep the old value until reload (see `constantsApi.getAll` dossier — process-local cache, no TTL).
- `default_membership_id` is a `TemporalProduct.uuid`, not a slug — the constants endpoint resolves it to `default_membership_slug` for clients. Sending a slug here will silently store garbage and break the public signup default until corrected.
- Logo is **not** updated through this method. `uploadLogo` (POST multipart) and `deleteLogo` (DELETE) are siblings; including `logo_url` in an `update` payload would write a string but skip the favicon regeneration that `upload_org_logo` triggers. Don't.
- `app_title` has `min_length=1, max_length=100` server-side; sending an empty string will 422. The branding form should validate before save.
- `register_rate_limit_*` only takes effect with a single uvicorn worker — see the `feedback_rate_limiter_single_worker` memory. Storing the values is fine; the in-memory limiter that reads them won't survive horizontal scaling. Admins editing these on a multi-worker deployment will see inconsistent enforcement.
- No optimistic-concurrency check. Two admins editing simultaneously: last write wins, no warning. Probably fine given the audience size, but worth knowing.

## Cross-cutting concerns

- **Auth**: bearer token + `_require_system_admin`. Non-admins get 403.
- **Constants propagation**: every successful branding update should be paired with `constantsManager.refresh()` on the client; downstream components re-render with new `org_name` / `app_title` / `timezone` / `logo_url`.
- **Timezone**: changing `timezone` retroactively reframes every datetime rendered through `lib/datetime.ts::formatInOrgTz`. Existing UTC-stored timestamps are unaffected; only their display shifts. Pre-2026-05-06 imports may be 4–5h off (see `feedback_naive_datetime_convention`) and that drift is independent of this field.
- **Email alerts**: `error_notify_email` feeds `services/error_alerts.py`; setting/clearing it here is the kill switch for the error-alert pipeline.
- **Audit**: none. The only audit trail is `OrgConfig.updated_at` (overwritten on every save) and git history of admin actions (there isn't one). If you need who-changed-what, build it.
- **Side effects**: backend mutation only. No websocket broadcast — other open admin sessions won't see the change until they reload or refetch.

## External consumers

None known. Web admin UI is the only caller. The Expo iOS app reads org config indirectly via `/api/constants` (unauthed) but does not write.

## Open questions

- Should the backend broadcast a config-changed event so other open clients invalidate their constants cache without a manual reload? Today, only the saving admin's session refreshes.
- `default_membership_id` has no FK constraint to `temporal_products` (it's a plain `String(36)`); should the handler validate it resolves to an active product before accepting the write?
