# Verification: circular_fk

sqlglot version: 30.8.0

## Pre-read prediction

Two migrations in order 001 → 002.

001 creates `post` with FK to `comment` (comment doesn't exist yet in the
reconciler state — but the reconciler never validates referential integrity,
it just stores the FK dict). FK survives intact.

002 creates `comment` with FK back to `post` (post already exists). Both
tables end up in the final state dict.

Note: the drop_table path in the reconciler GC's dangling FKs, but no DROP
TABLE occurs here, so GC does not fire. Both FKs survive.

Expected:
- 2 tables: `post`, `comment`
- `post` FK: featured_comment_id → comment(id)
- `comment` FK: post_id → post(id)
- No warnings

## Actual (post-run)

Both tests pass (2 passed). Prediction was exact:
- 2 tables `post` and `comment`, both surviving
- Each FK intact: post.featured_comment_id → comment(id), comment.post_id → post(id)
- No crash from circular reference
- No warnings

## Verdict

✓ First-try match.
