---
node_id: concorda-api::schemas/event_discount.py::EventDiscountRead
node_kind: schema
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 2f0886eac375bc9c74fc50cb2c88c027bf801b7a2efe7c9560844941e52af905
status: llm_drafted
---

# EventDiscountRead

## Purpose

Backend Pydantic admin read schema for `EventDiscount`. Serializes the full discount row including the `code` value — this is the privileged view returned by the three `events.edit`-gated admin endpoints (`GET/POST/PUT /api/events/{event_id}/discounts`). The public counterpart, `EventDiscountPublic`, exposes only `has_code: bool` on the registration page; `EventDiscountRead` is the one that gives administrators the actual string so they can share it. Future Claude editing this file should treat the Public/Read split as the boundary that keeps promo codes off the public wire.

## Invariants

- `code` is `Optional[str]` and rendered verbatim. This schema is for admin contexts only — never wire it into a route the public can reach. The slug-scoped `GET /api/events/slug/{slug}/discounts` uses `EventDiscountPublic`, not this; do not swap them.
- `ticket_ids` is derived from the `tickets` M2M relationship on the ORM object (source of truth per the EventDiscount model dossier); the legacy `ticket_ids` JSON column is only a fallback. The `extract_ticket_ids` `model_validator` must run before field validation — keep `mode="before"` and the `from_attributes = True` Config together.
- `uses: int` is required (not `Optional`); the ORM defaults it to `0` server-side, but if a future migration nullifies it, serialization will 500. Don't relax to `Optional` without backfilling.
- Shape parity with `EventDiscountUpdate`/`EventDiscountCreate` for the mutable fields — diverging field names here will silently break the round-trip on PUT.
- `discount_type` and `amount_type` are free-form `str` (no `Literal`), mirroring the model. Validation lives in callers; this schema is permissive on read by design.

## Gotchas

- **Public/Read confusion is the failure mode.** Both schemas hang off the same SQLAlchemy object and both define `extract_*` `model_validator`s with similar bodies. Swapping `response_model=EventDiscountRead` for `EventDiscountPublic` (or vice versa) is a one-character mistake that leaks codes. The EventDiscount model dossier flags this explicitly — don't cross the wires.
- The `model_validator` mutates `data.__dict__` in place rather than returning a dict. Subclassing or wrapping this schema in something that passes a plain dict (not an ORM object) will skip the M2M extraction silently — `ticket_ids` will be whatever the legacy JSON column held, which may be stale or empty.
- `ticket_ids` is `list[str] = []` with a default — an ORM object with `tickets=None` and a legacy column of `None` serializes to `[]`, not `None`. Callers diffing for "scoped vs unscoped" must use empty-vs-non-empty, not None checks.
- Single recorded commit (`6405007`) — no revert history yet. The Public/Read split is the design from day one, not a retrofit.

## Cross-cutting concerns

- **Auth**: All three consuming endpoints require `events.edit` permission plus `_require_event_org_scope` (caller must `can_administer_orgs` one of the event's organizing authorities, if any). Without that gate, the `code` field would be exposed to any logged-in user.
- **No audit / NotificationLog** entries are emitted when this schema is read or written; admin views of discount codes are not logged.
- **Payments coupling**: this schema is read-only and not touched by `routers/payments.py` (which queries the ORM directly for discount selection). Changing field names here will not break checkout, but renaming `code` would break the admin UI's ability to display the typed-in promo.

## External consumers

None known. Web admin UI is the only consumer; no Expo app surface, no webhooks, no scheduled jobs.

## Open questions

- Should `code` be masked (last 4 chars or `***`) even in the admin Read view, with a separate explicit "reveal" endpoint? Current design trusts anyone with `events.edit` to see all codes in plaintext on the list view.
- If `discount_type`/`amount_type` become proper enums on the model (per the EventDiscount dossier's open question), should this schema use `Literal["code","membership"]` / `Literal["flat","percent"]` to fail loudly on drift?
