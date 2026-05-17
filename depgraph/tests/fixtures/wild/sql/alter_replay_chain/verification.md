# Verification: alter_replay_chain

sqlglot version: 30.8.0

## Pre-read prediction

Seven migrations replayed in numeric order (001–007).

### event chain (001–006)

- 001: CREATE TABLE event(id, title) → event in state
- 002: ALTER ADD COLUMN tags → event(id, title, tags)
- 003: ALTER COLUMN tags TYPE VARCHAR(512) → type updated, columns unchanged
- 004: RENAME COLUMN tags TO tag_list → event(id, title, tag_list)
- 005: DROP COLUMN tag_list → event(id, title)
- 006: DROP TABLE event → event removed from state

After migration 006: `event` is absent.

### archive control (007)

Single text() call with two DDL statements separated by semicolon:
- CREATE TABLE archive(id, event_id, snapshot)
- ALTER TABLE archive ADD COLUMN archived_at TEXT

sqlglot.parse() splits on semicolons → two Operation objects from one text() call.
After migration 007: `archive(id, event_id, snapshot, archived_at)` is present.

### Final schema

- `event`: absent
- `archive`: columns `id`, `event_id`, `snapshot`, `archived_at`

No warnings (all SQL is static literal strings).

## Actual (post-run)

Both tests pass. Prediction was exact:
- `event` absent after 6-step chain (CREATE → ADD → ALTER TYPE → RENAME → DROP COL → DROP TABLE)
- `archive` present with columns `id`, `event_id`, `snapshot`, `archived_at`
- Two DDL statements in one text() call (migration 007) both parsed correctly
- No warnings

## Verdict

✓ First-try match.
