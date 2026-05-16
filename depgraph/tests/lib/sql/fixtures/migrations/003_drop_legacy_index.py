from sqlalchemy import text

def migrate(engine):
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX idx_users_email ON users(email)"))
