"""
Conspiracy Wiki MCP server — tier-gated.

MAX_TIER env var controls what this deployment can see:
  MAX_TIER=1 -> sees tiers 1,2,3   (MCP 1: everything)
  MAX_TIER=2 -> sees tiers 2,3     (MCP 2: mid + mainstream)
  MAX_TIER=3 -> sees tier 3 only   (MCP 3: mainstream only)

Access is cumulative from the "darkest" tier downward, per spec:
tier 1 = darkest/deepest, tier 3 = mainstream.
Lower MAX_TIER number = broader access.
"""
import os
import sqlite3
from mcp.server.fastmcp import FastMCP

MAX_TIER = int(os.environ.get("MAX_TIER", "3"))  # default = most restricted
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "db", "conspiracy.db"))

ALLOWED_TIERS = [t for t in (1, 2, 3) if t >= MAX_TIER]  # e.g. MAX_TIER=2 -> [2,3]

mcp = FastMCP(
    f"conspiracy-wiki-tier-{MAX_TIER}plus",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _tier_filter_sql():
    placeholders = ",".join("?" for _ in ALLOWED_TIERS)
    return placeholders, ALLOWED_TIERS


@mcp.tool()
def list_theories(category: str = "", limit: int = 50) -> list[dict]:
    """List conspiracy theories visible at this server's access tier.
    Optionally filter by category (e.g. 'government', 'ufo', 'health')."""
    placeholders, params = _tier_filter_sql()
    q = f"SELECT id, title, summary, tier, category FROM theories WHERE tier IN ({placeholders})"
    if category:
        q += " AND category = ?"
        params = params + [category]
    q += " ORDER BY id LIMIT ?"
    params = params + [limit]
    with _conn() as c:
        rows = c.execute(q, params).fetchall()
    return [dict(r) for r in rows]


@mcp.tool()
def search_theories(query: str, limit: int = 20) -> list[dict]:
    """Full-text search theories (title/summary/category) within this server's allowed tiers."""
    placeholders, params = _tier_filter_sql()
    with _conn() as c:
        rows = c.execute(
            f"""
            SELECT t.id, t.title, t.summary, t.tier, t.category
            FROM theories_fts f
            JOIN theories t ON t.id = f.rowid
            WHERE theories_fts MATCH ? AND t.tier IN ({placeholders})
            LIMIT ?
            """,
            [query] + params + [limit],
        ).fetchall()
    return [dict(r) for r in rows]


@mcp.tool()
def get_theory(theory_id: int) -> dict:
    """Get one theory by id, if it's within this server's allowed tiers."""
    placeholders, params = _tier_filter_sql()
    with _conn() as c:
        row = c.execute(
            f"SELECT id, title, summary, tier, category FROM theories WHERE id = ? AND tier IN ({placeholders})",
            [theory_id] + params,
        ).fetchone()
    if not row:
        return {"error": f"No theory with id={theory_id} accessible at this tier (allowed tiers: {ALLOWED_TIERS})"}
    return dict(row)


@mcp.tool()
def tier_info() -> dict:
    """Report which tiers this MCP deployment can access."""
    return {"max_tier_env": MAX_TIER, "allowed_tiers": ALLOWED_TIERS,
            "note": "tier 1 = darkest/deepest, tier 3 = mainstream. Access is cumulative from MAX_TIER down to 3."}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
