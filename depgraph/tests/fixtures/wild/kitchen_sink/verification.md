# Kitchen-Sink End-to-End Verification Log

**Date:** 2026-05-17  
**Verifier:** Claude (Sonnet 4.6)  
**Pipeline commit:** b17bcf29 + Task 6.5 additions

---

## Project inventory

### api/ (Python — FastAPI-shaped)

| File | Contributes |
|---|---|
| `migrations/0001_create_users.py` | schema: `users` (1 table) |
| `migrations/0002_create_events.py` | schema: `events` (1 table) |
| `migrations/0003_create_rsvps.py` | schema: `rsvps` (1 table) |
| `migrations/0004_create_tags.py` | schema: `tags`, `event_tags` (2 tables) |
| `migrations/0005_create_invites.py` | schema: `invites` (1 table) |
| `migrations/0006_create_waitlist_and_notifications.py` | schema: `waitlist`, `notifications` (2 tables) |
| `models/user.py` | model: `User` (extends `DeclarativeBase`, `__tablename__ = "users"`) |
| `models/event.py` | model: `Event` (extends `DeclarativeBase`, `__tablename__ = "events"`) |
| `models/rsvp.py` | model: `RSVP` (extends `DeclarativeBase`, `__tablename__ = "rsvps"`) |
| `models/tag.py` | model: `Tag` (extends `DeclarativeBase`, `__tablename__ = "tags"`) |
| `models/event_tag.py` | model: `EventTag` (extends `DeclarativeBase`, `__tablename__ = "event_tags"`) |
| `routers/events.py` | endpoints: `create_event` (@router.post), `list_events` (@router.get) |
| `routers/rsvps.py` | endpoint: `rsvp_event` (@router.post) |
| `routers/users.py` | endpoint: `list_users` (@router.get) |
| `routers/tags.py` | endpoint: `list_tags` (@router.get) |
| `services/events.py` | services: `create_event_service`, `list_events_service` (both have `db_access` edges) |
| `services/rsvps.py` | service: `rsvp_service` (`db_access` via `db.add(rsvp)`) |
| `services/users.py` | service: `list_users_service` (`db_access` via `db.query(User)`) |
| `utils/format.py` | utils: `format_date`, `build_event_url`, `parse_iso_date` |
| `utils/slug.py` | utils: `slugify`, `compute_rsvp_count` |
| `utils/validate.py` | util: `validate_email` |
| `tests/test_events.py` | tests: `test_create_event_service_returns_slug`, `test_list_events_service_returns_list` |
| `tests/test_utils.py` | tests: `test_format_date_strips_time`, `test_slugify_lowercases` |

### web/ (TypeScript — Next.js-shaped)

| File | Contributes |
|---|---|
| `components/EventList.tsx` | component: `EventList` (returns JSX `<div>`) |
| `components/EventCard.tsx` | component: `EventCard` (returns JSX `<div>`) |
| `components/RsvpButton.tsx` | component: `RsvpButton` (returns JSX `<button>`) |
| `hooks/useEvents.ts` | hook: `useEvents` (calls `useState`, `useEffect`) |
| `hooks/useCurrentUser.ts` | hook: `useCurrentUser` (calls `useState`, `useEffect`) |
| `__tests__/EventCard.test.tsx` | test: `EventCard.test.tsx` test function (`.test.tsx` file) |
| `__tests__/useEvents.test.ts` | test: `useEvents.test.ts` test function (`.test.ts` file) |

### db/ (placeholder)

Empty directory. Standalone `.sql` extractors are pinned out-of-scope per
`docs/known-limitations-v0.md`. The 3 originally-planned `db/*.sql` tables were
folded into migration 0004 and 0006 instead (keeping schema count at 8).

---

## Iterative build — distribution at each step

| Step | Files added | Cumulative distribution |
|---|---|---|
| Step 1 | 6 migration files | schema=8 |
| Step 2 | 5 model files | schema=8, model=5 |
| Step 3 | 4 router files (5 endpoints) | schema=8, model=5, endpoint=5 |
| Step 4 | 3 service files + 3 util files | schema=8, model=5, endpoint=5, service=4, util=6 |
| Step 5 | 2 TS component files + 1 hook file | (partial web) |
| Step 6 | All web files (components, hooks, tests) + Python tests | **schema=8, model=5, endpoint=5, service=4, util=6, component=3, hook=2, test=4** ✓ |

---

## Framework bugs found and fixed during authoring

Three bugs were found in `regen.py` (Task 6.1 code) while running iterative
checks. All are call-site mismatches between regen.py and the library functions
it calls — not classifier/extractor logic defects.

1. **`schema_to_primitives()` called with spurious `repo_key=` kwarg.**
   `reconcile_schema()` already embeds `repo_key` in the returned
   `SchemaPrimitive.id` fields; `schema_to_primitives()` takes no `repo_key`.
   Fix: removed `repo_key=repo_key` from the call.

2. **`attach_migration_attributes()` called positionally** but its signature
   uses keyword-only args (`*, primitives, migrations`).
   Fix: changed to keyword call.

3. **TS extractor path had spurious `"depgraph"` segment.**
   `tool_root` is already `depgraph/`, so `tool_root / "depgraph" / "extractors" / ...`
   produced a double-`depgraph` path that did not exist.
   Fix: removed the extra `"depgraph"` segment.

One framework config gap was also patched:

4. **`project_repos()` in `config.py` did not pass through `languages` and
   `migrations_dirs` keys.** The v2 regen path reads `info.get("languages")` from
   the dict returned by `project_repos()`, but those keys were silently dropped.
   Fix: added both keys as explicit passthrough fields in the returned dict.

---

## Import style discovery

Absolute imports using the `api.` prefix (e.g. `from api.services.events import ...`)
do not resolve because the extractor's `repo_path` is the `api/` directory itself,
so module paths are relative to it (e.g. `services/events.py` dotted as
`services.events`, not `api.services.events`). All inter-package imports in the
kitchen-sink use relative form (`from ..services.events import ...`) which the
Python extractor resolves correctly.

---

## Manual edge spot-check

Three edges picked from `nodes/_index/by_target.json` and traced back:

1. **`kitchen-sink-api::services/events.py::create_event_service`** has incoming
   `calls` edge from `kitchen-sink-api::routers/events.py::create_event`.
   Source: `routers/events.py` line calling `create_event_service(...)` — confirmed.

2. **`kitchen-sink-api::schema::events`** has incoming `references` edge from
   `kitchen-sink-api::models/event.py::Event` (via `__tablename__ = "events"`).
   Source: `models/event.py` — confirmed.

3. **`kitchen-sink-web::hooks/useEvents.ts::useEvents`** has calls edges to
   `external::npm::react::useState` and `external::npm::react::useEffect`.
   Source: `web/hooks/useEvents.ts` — both hooks called in body — confirmed.

---

## Observed kind distribution (final regen)

```
schema:    8  ✓
model:     5  ✓
endpoint:  5  ✓
service:   4  ✓
util:      6  ✓
component: 3  ✓
hook:      2  ✓
test:      4  ✓
```

All 8 target counts match.

---

## Test results

```
5/5 PASSED
  test_kitchen_sink_kind_distribution        PASS
  test_kitchen_sink_spot_check_classifications PASS
  test_kitchen_sink_no_orphan_edges          PASS
  test_kitchen_sink_models_reference_schemas PASS
  test_kitchen_sink_determinism              PASS
```

Determinism confirmed: two consecutive regens produce byte-identical node JSON
output (excluding `_meta.json` which contains a timestamp).

---

## Pinned behaviors / known quirks

- `db_access` edges from `create_event_service` and `rsvp_service` resolve to
  `external::unresolved::db_target` for the `db.add(entity)` calls. The db_access
  stub resolves `db.add(x)` only when `x` is a parameter with a type annotation
  that maps to a tracked ORM class; for locally-constructed instances (`event = Event()`)
  the argument to `db.add` is a variable, not the class itself, so it goes unresolved.
  `db.query(Event)` resolves correctly (argument is a class name). This is a known
  v0 limitation of the db_access stub (not a gate failure — test 4 only requires
  ≥1 db_access edge per service, and `list_events_service` / `list_users_service`
  satisfy this with exact `db.query` resolution).

- TS tests (`EventCard.test.tsx`, `useEvents.test.ts`) are classified via the
  `.test.tsx`/`.test.ts` filename pattern, not via `tests` edges — the TS test
  edge extractor uses `expect(...)` assertion scoping, and in these minimal stubs
  the asserted functions (`EventCard`, `useEvents`) are in the import-only set,
  not directly called inside an expect-assertion scope.
