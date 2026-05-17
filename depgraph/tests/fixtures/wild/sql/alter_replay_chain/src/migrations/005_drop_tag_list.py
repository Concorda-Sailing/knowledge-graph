from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE event DROP COLUMN tag_list"))
