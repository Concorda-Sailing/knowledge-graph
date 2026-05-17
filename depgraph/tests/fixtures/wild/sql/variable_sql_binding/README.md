# variable_sql_binding

## Pattern

A migration whose `text(...)` argument is a bare `Name`, not a string
literal. The DDL is named at module scope for readability — either via
plain `Assign` (`ACCOUNTS_DDL = "..."`) or `AnnAssign`
(`INVITES_DDL: str = "..."`) — and the function body passes the name to
`text()`.

```python
from sqlalchemy import text

ACCOUNTS_DDL = "CREATE TABLE accounts (id INTEGER PRIMARY KEY, ...)"
INVITES_DDL: str = "CREATE TABLE invites (id INTEGER PRIMARY KEY, ...)"

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text(ACCOUNTS_DDL))
        conn.execute(text(INVITES_DDL))
```

## Key behaviour under test

- `is_migration_file` returns True: `text()` call is present.
- `extract_migration` runs `_collect_string_bindings` over the module
  body and builds `{"ACCOUNTS_DDL": "...", "INVITES_DDL": "..."}`.
- Each `text(<Name>)` call resolves through `var_map` and parses normally.
- Both `accounts` and `invites` appear in the reconciled schema.
- No warnings emitted.

## Out of scope (intentionally deferred)

- `for k, v in TABLES.items(): text(v)` — loop-iteration over a known
  dict of literals. Needs flow-aware analysis; would unblock the
  Concorda `040_schema_redesign` pattern but is outside this fix.
- Names with more than one binding at module scope are dropped
  conservatively (see fixture `006_rebound_var.py` in the unit-test
  fixtures dir).

## sqlglot version

Tested against sqlglot 30.8.0.
