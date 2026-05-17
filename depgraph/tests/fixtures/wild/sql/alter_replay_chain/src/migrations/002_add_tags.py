from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE event ADD COLUMN tags TEXT"))
