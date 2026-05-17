"""Schema-qualified table names. `public.users` and `analytics.users` must
remain distinct primitives — collapsing both to `users` would mis-merge
schemas during reconciliation.
"""
from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text(
            "CREATE TABLE public.users (id INTEGER PRIMARY KEY, name TEXT)"
        ))
        conn.execute(text(
            "CREATE TABLE analytics.users (id INTEGER PRIMARY KEY, event TEXT)"
        ))
        conn.execute(text(
            "ALTER TABLE public.users ADD COLUMN email TEXT"
        ))
