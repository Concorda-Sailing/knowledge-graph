from sqlalchemy import text

def migrate(engine, cols):
    cols_sql = ", ".join(cols)
    # Dynamic interpolation — extractor should record a warning, not parse.
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE dynamic ({cols_sql})"))
