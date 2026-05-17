# circular_fk

## Pattern

Two tables with foreign keys pointing at each other — a genuine circular
reference that cannot exist in a freshly-ordered schema without deferrable
constraints, but that appears in practice when tables are created separately
and FKs are added later, or when the DB engine supports deferred FK checks.

Migration 001 creates `post` with an FK to `comment` (which doesn't exist yet).
Migration 002 creates `comment` with an FK back to `post`.

```sql
-- 001_create_post.py
CREATE TABLE post (
    id INTEGER PRIMARY KEY,
    body TEXT NOT NULL,
    featured_comment_id INTEGER,
    FOREIGN KEY (featured_comment_id) REFERENCES comment(id)
);

-- 002_create_comment.py
CREATE TABLE comment (
    id INTEGER PRIMARY KEY,
    post_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES post(id)
);
```

## Key behaviour under test

- The parser accepts both FK declarations without error.
- The reconciler replays both migrations without crashing.
- Both tables survive with their FK metadata intact.
- The reconciler does NOT do referential integrity checking — it is a
  structural replay engine, not a constraint validator.

## Expected final schema

- `post`: columns `id`, `body`, `featured_comment_id`; FK → `comment(id)`
- `comment`: columns `id`, `post_id`, `content`; FK → `post(id)`

## sqlglot version

Tested against sqlglot 30.8.0.
