from sqlalchemy import text


def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE event"))
