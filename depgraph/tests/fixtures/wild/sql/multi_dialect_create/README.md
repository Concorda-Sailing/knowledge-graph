# multi_dialect_create

## Pattern

Three migration files that create the same logical table (`product`) using
syntax from three different SQL dialects:

- `001_sqlite.py` — SQLite idioms: `INTEGER PRIMARY KEY`, `TEXT`, `REAL`
- `002_postgres.py` — Postgres idioms: `SERIAL PRIMARY KEY`, `VARCHAR(255)`, `NUMERIC(10,2)`
- `003_mysql.py` — MySQL idioms: `INT AUTO_INCREMENT PRIMARY KEY`, `DECIMAL(10,2)`

All three should reconcile to a single `product` table. The first migration
(ordered 001) wins for CREATE; the subsequent ones hit the `if_not_exists`
branch (since each uses `CREATE TABLE IF NOT EXISTS`) and are silently skipped.

## Key behaviour under test

- `extract_migration` parses all three files using sqlglot's default dialect
  (`sqlite`). Dialect-specific type keywords (`SERIAL`, `NUMERIC`) that
  sqlglot can still tokenise even in sqlite mode survive and appear as their
  parsed type string.
- `reconcile_schema` applies migrations in numeric order; 002 and 003 are
  no-ops because `IF NOT EXISTS` is set and the table already exists.
- Final schema matches the **SQLite file** (migration 001), since that one
  actually performs the CREATE.

## Column names expected after reconciliation

`id`, `name`, `price`, `stock`

## sqlglot version

Tested against sqlglot 30.8.0.
