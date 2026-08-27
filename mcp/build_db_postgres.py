import os
import psycopg2
from data import THEORIES

DATABASE_URL = os.environ["DATABASE_URL"]  # e.g. postgres://user:pass@host:5432/conspiracy_db

entries = THEORIES[:200]

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

with open(os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")) as f:
    cur.execute(f.read())

cur.execute("TRUNCATE theories RESTART IDENTITY")
for title, summary, tier, category in entries:
    cur.execute(
        "INSERT INTO theories (title, summary, tier, category) VALUES (%s,%s,%s,%s)",
        (title, summary, tier, category),
    )

conn.commit()
cur.close()
conn.close()
print(f"Inserted {len(entries)} theories into Postgres.")
