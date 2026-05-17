# alter_replay_chain

## Pattern

Six migrations that exercise the full ALTER TABLE lifecycle for an `event` table,
plus a parallel `archive` table that stops before the DROP to serve as a control
confirming incremental reconciliation works.

### event chain (migrations 001–006)

```
001: CREATE TABLE event (id INTEGER PRIMARY KEY, title TEXT NOT NULL)
002: ALTER TABLE event ADD COLUMN tags TEXT
003: ALTER TABLE event ALTER COLUMN tags TYPE VARCHAR(512)
004: ALTER TABLE event RENAME COLUMN tags TO tag_list
005: ALTER TABLE event DROP COLUMN tag_list
006: DROP TABLE event
```

After replaying all six migrations, `event` is absent from the schema.

### archive control (migration 007)

```
007: CREATE TABLE archive (id INTEGER PRIMARY KEY, event_id INTEGER, snapshot TEXT NOT NULL)
     ALTER TABLE archive ADD COLUMN archived_at TEXT
```

(Both DDL statements are in a single `text()` call in migration 007.)

After replaying, `archive` has columns: `id`, `event_id`, `snapshot`, `archived_at`.

## Key behaviour under test

- CREATE → ADD COLUMN → ALTER TYPE → RENAME COLUMN → DROP COLUMN → DROP TABLE
  replays cleanly with 0 surviving rows for `event`.
- ADD COLUMN followed by no DROP → column persists in `archive`.
- Reconciler does not crash on any step, even with intermediate column renames
  and type changes.

## Expected final schema

- `event`: absent (dropped in migration 006)
- `archive`: columns `id`, `event_id`, `snapshot`, `archived_at`

## sqlglot version

Tested against sqlglot 30.8.0.
