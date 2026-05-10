---
node_id: concorda-api::models/org_config.py::OrgConfig
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: a8b0b022aedddb5a16a8ffd72844986587d3257770d290ac953eabda6726ece9
status: current
---

# OrgConfig

## Purpose

The singleton SQLAlchemy row that holds every per-deployment org setting Concorda needs at runtime: branding (`org_name`, `app_title`, `logo_url`), display tz (`timezone`), public-signup default plan (`default_membership_id`), the in-memory registration rate limiter's tunables (`register_rate_limit_max`, `register_rate_limit_window_seconds`), and the error-alert pipeline's recipient + cooldown (`error_notify_email`, `error_notify_cooldown_seconds`). Exactly one row per deployment — handlers read with `db.query(OrgConfig).first()` and create it on first write if missing. This is the upstream of `GET /api/constants` (which fans out to ~30 components via `useConstants()`), the admin org-config CRUD trio, the ICS schedule feed (timezone), and the crew invite/confirm email flows. If you're adding an org-level knob that admins should toggle without a deploy, this is where it lives.

## Invariants

- Singleton: query with `.first()`, never `.all()`. The handler in `routers/admin.py:973` instantiates a fresh `OrgConfig()` on first save — no migration seeds it. Code paths that read must tolerate `None` (see `routers/admin.py:957-959` returning a hardcoded fallback, and `routers/constants.py:132` which also handles missing).
- Defaults are duplicated as `default=` (Python-side) and `server_default=` (DDL) for fields added after initial schema (`app_title`, `register_rate_limit_*`, `error_notify_cooldown_seconds`). Keep both in sync when adding columns or existing rows on older deployments will deserialize as `None` for non-nullable columns and blow up.
- `timezone` is a string IANA zone name (`"America/New_York"` default), consumed by `lib/datetime.ts::formatInOrgTz` on the web and by the ICS feed generator. Not validated at write time — sending garbage will silently break formatters.
- `default_membership_id` is a `TemporalProduct.uuid` stored as plain `String(36)` — **no FK constraint**. Constants endpoint resolves it to `default_membership_slug` for clients; an invalid UUID stores fine and breaks the public signup default until corrected.
- `error_notify_email` nullable; empty/`None` is the kill switch for `services/error_alerts.py`. Admin update handler maps `""` → `None`.
- `updated_at` auto-bumps via `onupdate=datetime.utcnow` — naive UTC, consistent with the codebase's `UtcDateTime` convention (see `feedback_naive_datetime_convention`).

## Gotchas

- Adding a new column requires both `default=` and `server_default=` plus an Alembic migration; older deployments updating in place have no row, and on a fresh write SQLAlchemy uses Python defaults but pre-existing rows on staging/prod need the DDL default to backfill.
- `register_rate_limit_*` are honored only under a single uvicorn worker — the in-memory dicts in `auth.py` don't survive `--workers` or horizontal scaling (see `feedback_rate_limiter_single_worker`). Storing the values is harmless on multi-worker; enforcement is not.
- No optimistic concurrency. Two admins editing simultaneously: last write wins silently. `updated_at` is the only audit trail and gets overwritten on every save.
- Logo writes do **not** go through the generic update path — `POST /api/admin/org-config/logo` and `DELETE /api/admin/org-config/logo` regenerate the favicon as a side effect. Setting `logo_url` via the SQL row directly skips that.
- `org_name` defaults to `"MBSA"`, `app_title` to `"MBSA Clubhouse"` — the model is multi-tenant-shaped but MBSA-flavored. A second deployment must overwrite both on first boot.
- Recent commits are all additive (rate-limit fields, app_title, default-membership, error-alert recipient). No destructive migrations yet — pattern is "add nullable-or-defaulted column, surface to admin UI, surface to constants if clients need it."

## Cross-cutting concerns

- **Auth**: model itself is unscoped; the gate is at the router layer (`_require_system_admin` for mutations; `GET /api/constants` is unauthenticated and exposes a curated subset).
- **Constants propagation**: every field added here that clients should see must also be added to `routers/constants.py::ConstantsResponse` and the web `AppConstants` type — and admin save handlers must call `constantsManager.refresh()` or open sessions stay stale (see `constantsApi.getAll` dossier — process-local cache, no TTL).
- **Email pipeline**: `error_notify_email` feeds `services/error_alerts.py`; crew invite/confirm flows in `routers/events.py:2580,2917` read `OrgConfig` for branding in outbound mail.
- **Calendar feed**: `routers/calendar.py:329` reads `timezone` to stamp the ICS `X-WR-TIMEZONE` header — changing tz retroactively reframes every subscribed calendar.
- **Side effects**: pure data row, no triggers or websocket broadcast on update.

## External consumers

None known directly. The Expo iOS app reads org settings via the unauthed `/api/constants` endpoint. No webhooks or scheduled jobs read this row.

## Open questions

- Should `default_membership_id` get an FK to `temporal_products` and a check that the product is active? Today an admin can save a stale UUID and silently break public signup.
- Is the singleton pattern still right if/when Concorda hosts a second org? The model has no `organization_id` — multi-tenancy would require a schema break or a per-`Organization` config row.
