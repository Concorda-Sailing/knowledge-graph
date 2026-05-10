---
node_id: GET::/api/tracking/email-open/{0}
node_kind: endpoint
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: bd4127c79fb71676e3251721b7606f1151f636bbbd9cf8060e1a24bd60b6873b
status: llm_drafted
---

# GET /api/tracking/email-open/{token}

## Purpose

Records the first time a user opens a crew invitation email by setting the `opened_at` timestamp. It serves as a transparent 1×1 pixel tracking endpoint that returns a base64-encoded GIF to prevent broken image icons in email clients. This is distinct from explicit event tracking; it is a passive listener triggered by the loading of the image in a mail client.

## Invariants

- **Returns a 1×1 transparent GIF.** The response body must be the `_TRANSPARENT_GIF` constant to ensure valid image rendering.
- **Uses `image/gif` media type.**
- **Implements `no-cache` headers.** The response includes `Cache-Control: no-store, no-cache, must-revalidate` to ensure the browser/client does not cache the pixel, which would prevent subsequent tracking if the logic ever evolves beyond the first hit.
- **Single-write constraint.** The `opened_at` field is only updated if it is currently `None`.

## Gotchas

- **The `token` is a UUID-based string.** The token is sourced from `notification_logs.tracking_token` and is generated during the crew invitation flow.
- **The endpoint is idempotent regarding the database state.** Once `log.opened_at` is set, subsequent calls with the same token result in a no-op (the `if log and log.opened_at is None` guard).

## Cross-cutting concerns

- **Auth**: None (the token itself acts as the authorization mechanism for the event).
- **Audit**: Y (updates `NotificationLog.opened_at`).
- **Side effects**: Updates the status of crew invitations in the notification system.

## External consumers

Email clients (via embedded `<img>` tags in crew invitation emails).

## Open questions

- Should we add a fallback for when the token is invalid or the log is not found, or is the silent return of the GIF sufficient for the current UX?
