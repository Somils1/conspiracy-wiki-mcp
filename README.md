# Conspiracy Wiki — Tiered MCP Project

Same pattern as the personal knowledge-graph project (vault → db → MCP),
applied to a 200-entry conspiracy-theory wiki, split into 3 access tiers
and exposed via 3 separately deployable MCP servers.

## Tier definitions

| Tier | Meaning (per TL spec)                  | Count |
|------|-----------------------------------------|-------|
| 1    | Darkest / most extreme (still real, documented — declassified programs, unsolved-death theories, cover-up allegations) | 84 |
| 2    | Basic / moderately darker                | ~93 |
| 3    | Basic, mainstream (Moon landing, Bigfoot, etc.) | ~23 |

**Scope note:** hate-speech-based conspiracies (antisemitic tropes,
Holocaust denial, "great replacement," etc.) and anything that reads as
a call to violence are excluded at every tier — that line doesn't move
regardless of how "dark" a tier is supposed to be.

## Access matrix (cumulative, per spec)

| MCP | MAX_TIER env | Sees tiers |
|-----|--------------|------------|
| MCP 1 | `1` | 1, 2, 3 (everything) |
| MCP 2 | `2` | 2, 3 |
| MCP 3 | `3` | 3 only |

Same codebase (`mcp/server.py`) for all three — only the `MAX_TIER` env
var differs. Each has its own SQL filter, so an MCP-3 deployment
literally cannot query tier-1 rows; it's not just hidden in the UI.

## Files

- `mcp/data.py` — the 200 curated theories with title/summary/tier/category
- `db/schema.sql` — Postgres schema (theories table + generated tsvector search column)
- `mcp/build_db_postgres.py` — loads the 200 theories into a Postgres DB (`DATABASE_URL` env var)
- `mcp/server_postgres.py` — the tiered FastMCP server, Postgres-backed (4 tools: `list_theories`, `search_theories`, `get_theory`, `tier_info`)
- `vault/*.md` — 200 Obsidian-style notes, one per theory (still generated locally via `mcp/build_db.py` if you want the vault files; SQLite version kept as `server.py`/`build_db.py` if you ever want a fully local/offline variant)
- `Dockerfile` — single image; all 3 deployed services run this image, connecting to the SAME shared Postgres instance, differing only in `MAX_TIER`
- `render.yaml` — Render blueprint: 1 managed free Postgres DB + 3 web services

## Local build/test (Postgres)

Requires a Postgres instance — easiest is a free one from [Neon](https://neon.tech) or [Supabase](https://supabase.com) if you don't want to install Postgres on Windows.

```powershell
cd conspiracy-wiki-mcp
pip install -r requirements.txt

$env:DATABASE_URL = "postgres://user:pass@host:5432/conspiracy_db"
cd mcp
python build_db_postgres.py    # creates schema + loads 200 rows

$env:MAX_TIER = "1"
python server_postgres.py      # runs on :8000
```

## Deploying (so it's NOT local — required for the task to count)

**Render (recommended — one blueprint does everything):**
1. Push this folder to a GitHub repo.
2. On Render: **New +** → **Blueprint** → select the repo.
3. Render reads `render.yaml` and provisions:
   - 1 free managed Postgres DB (`conspiracy-db`)
   - 3 web services, each auto-wired to that same DB via `DATABASE_URL`, differing only in `MAX_TIER`
4. After the DB is live, run the loader once (Render Shell tab on any of the 3 services, or from your machine with the DB's external connection string):
   ```powershell
   $env:DATABASE_URL = "<external connection string from Render dashboard>"
   python mcp/build_db_postgres.py
   ```
5. All 3 services now serve the same DB, filtered by tier. Grab the 3 public URLs from the Render dashboard.

**Fly.io alternative:** use Fly Postgres (`fly postgres create`) for the shared DB, then `fly deploy` each of the 3 apps with `DATABASE_URL` and `MAX_TIER` set per app — same idea, different platform.


Once deployed, register each URL as its own MCP connector — MCP 1's URL
for full access, MCP 2's for the mid tier, MCP 3's for the public/basic
demo — which is what actually satisfies "not local."

## Wiring into Claude / MCP clients

Each deployed URL is a standard streamable-HTTP MCP endpoint — add it as
a remote connector the same way you'd add any other MCP server, pointing
at `https://<service>.onrender.com` (or your Fly app URL). No local
ingestion step needed — the DB is already baked into each container at
build time.
