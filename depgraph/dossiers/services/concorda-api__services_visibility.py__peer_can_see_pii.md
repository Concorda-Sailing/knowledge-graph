---
node_id: concorda-api::services/visibility.py::peer_can_see_pii
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 567b6ad8057bd1aef02766762a80d07874c1c7abc599c088191f8fa7f854118e
status: current
---

# peer_can_see_pii

## Purpose

Determines if a viewer is authorized to see the PII (name, email, phone, picture) of a specific person. It implements the logic for the `rule::crew_visibility::peer_pii_resume_gated` rule, acting as a gatekeeper for sensitive data in crew lists. Use this function instead of manual attribute checks to ensure consistent masking of user data across the API.

## Invariants

- **Returns a boolean.** Always returns `True` or `False`.
- **`viewer_is_owner` is the master override.** If this is `True`, the function returns `True` immediately, bypassing all other checks.
- **Self-view is always allowed.** If `viewer_id == target_person_id`, the function returns `True`.
- **Relies on `has_published_resume` for peer access.** If the viewer is not the owner or the target, visibility is strictly tied to the target's resume publication status.
- **Does not handle administrative elevation.** Admins and Event Managers must pass `viewer_is_owner=True` to ensure they bypass the gate.

## Gotchas

- **Semantic bypass required for admins.** This function does not check for admin roles; it only checks ownership or identity. Per the docstring, callers like `event-manager` must explicitly set `viewer_is_owner=True` to see unfiltered data.
- **Recent refactor dependency.** Per commit `ea4fcb2`, this logic was extracted to harden `confirm_event_crew`. Any changes to the visibility logic must be verified against the `confirm_event_crew` flow to ensure no regression in crew confirmation stability.

## Cross-cutting concerns

- **Auth**: Relies on the caller to correctly identify if the viewer is the owner or an admin (via `viewer_is_owner`).
- **Side effects**: Directly affects the data shape of the `GET /api/events/{0}/sailing-event/crew` response.

## External consumers

- `GET /api/events/{0}/sailing-event/crew` (via `routers/events.py:2400`).
