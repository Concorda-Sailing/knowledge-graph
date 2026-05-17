# schema_qualified_names

`CREATE TABLE public.users` and `CREATE TABLE analytics.users` must produce
two distinct schema primitives, and `ALTER TABLE public.users ...` must apply
to the right one.

## Pattern

Postgres-style two-part names (`<schema>.<table>`). sqlglot parses these into
a `Table` node where `.name` is the local part (`users`) and `.db` is the
schema prefix (`public` / `analytics`).

## Why tracked

Before the fix, every table-name extraction site in `lib/sql/parser.py`
called `node.this.name` (or similar) without consulting `.db`. Two real
tables in different schemas collapsed to the same primitive key, and a
subsequent `ALTER TABLE public.users ADD COLUMN email` was applied to
whichever `users` row happened to be reconciled — non-deterministic merge
behaviour.

## v0 behavior

A `_qualified_table_name(node)` helper returns `"<db>.<name>"` when the
schema qualifier is present, else just `"<name>"`. Every Table/Schema-node
read in `_handle_create`, `_handle_alter`, `_handle_drop`, the index path,
the view path, and the FK reference paths runs through the helper, so
reconciliation keys schemas correctly across qualifier-mixed migrations.
