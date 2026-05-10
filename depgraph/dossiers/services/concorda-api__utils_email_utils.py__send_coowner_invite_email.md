---
node_id: concorda-api::utils/email_utils.py::send_coowner_invite_email
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 524b9cf0da3a60c2513dac0fc571bb98ffaa142d236fb972fe2466549329ac2a
status: llm_drafted
---

# send_coowner_invite_email

## Purpose

Sends a formal invitation to an existing member to become a co-owner of a specific boat. It utilizes `_coowner_email_ctx` to gather necessary context (boat status, names, and URLs) and renders a managed template via `render_email_template`. This is a specialized version of the general email dispatching logic, specifically tailored for the co-ownership lifecycle.

## Invariants

- **Requires a valid `db: Session`** to resolve boat status and context.
- **Uses the `coowner_invite` template key** via `render_email_template`.
- **Requires `boat_id`** to correctly render the `_render_boat_status_block` within the email context.
- **Returns `None`**; the function is a side-effect-only service.

## Gotchas

- **Template-driven content:** Per commit `05d60a6`, all user-facing emails must use managed templates; do not attempt to pass raw HTML or custom strings to `send_email` directly if you want to maintain the current design pattern.
- **Context dependency:** The function relies on `_render_boat_status_block` to inject the `boat_status_block` into the context; if the boat status rendering logic changes, the email content will change.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: Y (via `send_email` and `db` session interaction)
- **Rate limit**: none
- **Side effects**: Triggers the "co-owner invite" flow which is part of the broader `feat(coowner)` lifecycle.

## External consumers

None known.
