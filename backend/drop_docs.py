from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS documents CASCADE;"))
    conn.commit()
    print("Table documents dropped.")
