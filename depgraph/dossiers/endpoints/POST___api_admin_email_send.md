---
node_id: POST::/api/admin/email/send
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 72cd1f8f777b400f5268d097a9d9091aa2055cfc1b5ce22df1a998113e8789de
status: llm_drafted
---

# POST /api/admin/email/send

## Purpose

Sends bulk email notifications to members based on membership class or organization delegates. It allows admins to either provide a raw subject/body or use a pre-existing `EmailTemplate`. This endpoint is distinct from standard transactional emails as it is designed for high-volume broadcasts to specific audience segments.

## Invariants

- **Requires `require_auth`** — The caller must be an authenticated user with admin privileges.
- **Input shape** — Expects `BulkEmailRequest` containing either `template_id` or direct `subject`/`body` strings.
- **Audience requirement** — Must provide at least one of `product_ids` or `include_delegates` to prevent empty broadcasts.
- **Rate limit behavior** — The endpoint enforces a per-user limit of 5 requests per 1-hour window (`_BULK_EMAIL_RATE_LIMIT_MAX`).

## Gotchas

- **Rate limit bypass in tests** — The rate-limiting logic is wrapped in a `CONCORDA_ENV != "test"` check; ensure tests do not rely on this limit to verify error handling unless the environment is explicitly set.
- **Security/Privilege Escalation** — Per commit `650233f`, this endpoint is a sensitive admin-only path; any change to the `require_auth` dependency or the router's mounting point could expose bulk messaging to non-admin users.
- **Recipient Filtering** — The logic filters for `Person.leave_date == None`. If a user has a leave date set, they are excluded from the `product_ids` broadcast, but the behavior for `include_delegates` relies on the `steward_id` presence in the `Organization` table.

## Cross-cutting concerns

- **Auth**: Requires `require_auth` (admin-level access).
- **Rate limit**: Enforced via `_bulk_email_rate_limit` (5 requests per 3600s window).
- **Audit**: `ActivityMiddleware` records the access; the function also logs a warning with recipient count and audience for incident review.
- **Side effects**: Used by the admin dashboard to broadcast notifications to members and club stewards.

## External consumers

- `concorda-web::src/lib/api.ts::adminEmailConfigApi.sendBulk`
