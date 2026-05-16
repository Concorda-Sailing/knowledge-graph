from sqlalchemy import text

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50)"))
