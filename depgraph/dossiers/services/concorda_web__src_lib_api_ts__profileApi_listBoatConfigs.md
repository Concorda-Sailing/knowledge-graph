---
node_id: concorda-web::src/lib/api.ts::profileApi.listBoatConfigs
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: ad8b7c91656313a3e19271f1e92eaa33f731f150f9e1f3fcbd9ac3b68d9d3861
status: current
---

# profileApi.listBoatConfigs

## Purpose
Client-side mirror for listing all BoatConfigs (named position layouts — e.g. "Spinnaker", "No-Spin", "Delivery") attached to a boat. GETs `/api/profile/boats/{boatId}/configs` and returns `BoatConfig[]` ordered by `(sort_order, name)`. This is the read-side counterpart to `createBoatConfig`/`updateBoatConfig`/`deleteBoatConfig`. It's the lookup that lets the boat-positions form render existing layouts, lets the schedule new-event boat picker resolve a `boat_config_id` back to a position layout, and lets the dashboard event-plan panel show the trim/delivery options when planning a regatta. **Owner-only read** — the backend gates with `_require_boat_owner`, identical to the create path; non-owner crew cannot list, even if they're rostered on the boat.

## Invariants
- `boatId` must be a Boat where the current user has an active `BoatCrew` row with `role="owner"` — otherwise 403, not 200-with-empty-list. Callers must handle the throw (all three current consumers wrap in try/catch and fall back to `[]`).
- Server-side ordering is `(sort_order ASC, name ASC)`. Clients should not re-sort unless they explicitly intend a different presentation.
- Every config in the response carries `id`, `boat_uuid`, `name`, `config_type`, `positions[]`, `is_default`, `sort_order`, timestamps.
- At most one `is_default=true` per boat (enforced by create/update, assumed here).
- Empty array is a legitimate response — a boat may have zero configs (especially newly created boats before `boat-positions-config` runs its seed-default branch).

## Gotchas
- `boat-positions-config.tsx:100` auto-seeds preset configs (Spinnaker/No-Spin/Delivery) when the list is empty AND viewer is owner. That call path POSTs into `createBoatConfig` from inside the list-fetch callback — refactoring this fetch to `useQuery` etc. needs to preserve the seed-on-empty side effect.
- `bf15808` ("use stored boat_config_id instead of shape-matching") landed because the schedule pages used to identify "the matching config" by comparing `positions_needed` shapes against each config in the list. The legacy shape-match is still fallback code (`page.tsx:285`, `event-plan-panel.tsx:144`) for events saved before `boat_config_id` existed — when editing those callers, do not delete the fallback without a migration audit.
- `b4d60c6` cemented that `position.count ?? 1` is the slot-count expansion rule when iterating positions returned from this list. Any consumer skipping the `?? 1` will under-count.
- 403s look identical to network errors to the catch handler — silent fallback to `[]` may mask a permissions regression. Worth logging in dev.

## Cross-cutting concerns
- **Auth:** `require_auth` + `_require_boat_owner`. Co-owners with `role="owner"` qualify; crew/`accepting_crew` rows do not.
- **No mutation, no audit, no websocket emission.**
- **Cache discipline:** none of the three consumers memoize across boats — switching boats in event-plan-panel re-fetches every time. Acceptable today (small N), but a future React Query layer should key on `boatId`.
- **Downstream coupling:** the returned `boat_config_id` is what gets stored on `SailingEvent.boat_config_id`; the list is the lookup table for resolving that FK back to a renderable layout.

## External consumers
None known. Three direct UI dependents in concorda-web (boat-positions-config form, schedule detail boat-picker, dashboard event-plan-panel). No mobile/Expo, no scheduled job, no webhook usage observed.

## Open questions
- Should non-owner crew (or `accepting_crew` invitees) be able to *read* configs so they can see "this is what positions exist on this boat"? Today the answer is no, which forces the schedule detail page to special-case owner-vs-crew rendering.
- The list endpoint has no pagination or filter (e.g. `config_type=spinnaker`). With no per-boat cap on configs, a heavy-user boat could in theory return a large array — not a concern at current scale.
