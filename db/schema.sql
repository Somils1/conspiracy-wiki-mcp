CREATE TABLE IF NOT EXISTS theories (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    tier INTEGER NOT NULL CHECK (tier IN (1,2,3)),
    category TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tier ON theories(tier);

-- full text search index (Postgres native, replaces SQLite FTS5)
ALTER TABLE theories ADD COLUMN IF NOT EXISTS search_vector tsvector
    GENERATED ALWAYS AS (to_tsvector('english', title || ' ' || summary || ' ' || category)) STORED;

CREATE INDEX IF NOT EXISTS idx_theories_search ON theories USING GIN (search_vector);
