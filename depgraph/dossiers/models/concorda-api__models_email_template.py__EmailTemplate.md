---
node_id: concorda-api::models/email_template.py::EmailTemplate
node_kind: model
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 6cce72a82fd0b757e005e5c71c7896f8c2435c9a209358bfd343b3920494c500
status: current
---

# EmailTemplate

## Purpose

Backend SQLAlchemy model for an admin-editable email template. Each row is one transactional template (welcome, invite, password reset, crew calendar, approval requests, etc.) with a unique slug `name`, a `subject`, an HTML `body`, and a `variables` JSON list documenting the placeholders the body expects. Admins edit these via `routers/admin.py`; the transactional pipeline reads them through `utils.email_utils.render_email_template(name, vars, db)` rather than hard-coding copy in Python.

## Invariants

- `name` is unique and is the public lookup key — callers pass slugs like `"crew_invitation"`, not IDs.
- Only rows with `is_active=True` are renderable. `render_email_template` raises `ValueError` on missing-or-inactive so failures surface in `NotificationLog` instead of silently sending a half-rendered email.
- Placeholder syntax is Jinja-style `{{var}}` (with optional whitespace), not Python `{var}` — see `_PLACEHOLDER_RE` in `utils/email_utils.py`.
- `app_title` and `support_email` are auto-injected by the renderer; templates may reference them without callers plumbing them through. Caller-supplied vars win on collision.
- Substitution is single-pass: a substituted value containing literal `{{otherkey}}` is NOT re-expanded. Pre-rendered HTML blocks (e.g. `boat_status_block`) rely on this.
- The `email_templates` table is in `_PRESERVE_TABLES` in `tests/conftest.py` — it survives the per-test wipe so seed migrations don't have to re-run.

## Gotchas

- The `variables` column is documentation, not enforcement. Nothing validates that the body's placeholders match the list, or that callers pass everything the body needs. Missing keys leave `{{key}}` in the rendered output and only log a warning.
- Templates are seeded/upserted by migrations (`041`, `042`, `043`, `074`–`078`, `084`). Editing copy in a migration after it has run on prod has no effect — write a new migration that updates by `name`, the way `084_event_crew_email_templates.py` does.
- Admin edits persist across deploys (data migrations don't re-mutate; see deploy memory). A migration that hard-overwrites `body` would clobber an admin's edits — prefer insert-if-missing.
- The model's `__init__` hard-codes `type="EmailTemplate"` for the polymorphic BaseModel; don't pass `type=` from callers.

## Cross-cutting concerns

- Sole input to `utils.email_utils.render_email_template`, which is the chokepoint for all transactional email subject/body rendering (welcome, password reset, crew invites, co-owner invites, approval notifications, event-crew responses, fleet comms, regatta reminders).
- Render failures should land in `NotificationLog` as `failed` rows rather than crashing the request — wired in `services/approval_notifications.py` and the various `email_utils` senders.
- Admin CRUD lives at `/admin/email-templates` (`routers/admin.py`); preview endpoint runs the production render path so `app_title`/`support_email` injection is honored.
- Behavioral coverage: `tests/test_email_send_scenarios.py` renders every active template with synthesized realistic vars and asserts no `{{leftover}}` placeholders remain.

## External consumers

None outside the repo. All consumption is server-side via `render_email_template`.

## Open questions

- Should `variables` be enforced (reject render when caller omits a declared var) instead of just warning? Would catch typos at write time but breaks the "extra placeholders are fine" pattern used for optional blocks.
- No per-org templates yet — single global table. If multi-tenant copy customization is ever needed, `name` uniqueness becomes `(organization_id, name)`.
