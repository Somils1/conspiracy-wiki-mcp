import sqlite3, os, re
from data import THEORIES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "db", "conspiracy.db")
VAULT_DIR = os.path.join(ROOT, "vault")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(VAULT_DIR, exist_ok=True)

entries = THEORIES[:200]  # top 200 per original brief

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS theories")
cur.execute("""
CREATE TABLE theories (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    tier INTEGER NOT NULL CHECK (tier IN (1,2,3)),
    category TEXT NOT NULL
)
""")
cur.execute("CREATE INDEX idx_tier ON theories(tier)")
cur.execute("CREATE VIRTUAL TABLE theories_fts USING fts5(title, summary, category, content='theories', content_rowid='id')")

for i, (title, summary, tier, category) in enumerate(entries, start=1):
    cur.execute("INSERT INTO theories (id, title, summary, tier, category) VALUES (?,?,?,?,?)",
                (i, title, summary, tier, category))
cur.execute("INSERT INTO theories_fts(rowid, title, summary, category) SELECT id, title, summary, category FROM theories")
conn.commit()

def slug(s):
    return re.sub(r"[^\w\- ]", "", s).strip()

for i, (title, summary, tier, category) in enumerate(entries, start=1):
    fname = os.path.join(VAULT_DIR, f"{slug(title)}.md")
    with open(fname, "w") as f:
        f.write(f"---\nid: {i}\ntier: {tier}\ncategory: {category}\n---\n\n# {title}\n\n{summary}\n\nTier: {tier} | Category: {category}\n")

print(f"Inserted {len(entries)} theories into {DB_PATH}")
print(f"Wrote {len(entries)} vault notes into {VAULT_DIR}")
