"""
Conspiracy Wiki MCP server — Postgres-backed, tier-gated.

Same tier logic as server.py (SQLite version), but all 3 deployed MCP
services point at ONE shared Postgres database via DATABASE_URL —
they differ only in MAX_TIER, not in which data file they carry.
"""
import os
import psycopg2
import psycopg2.extras
from mcp.server.fastmcp import FastMCP

MAX_TIER = int(os.environ.get("MAX_TIER", "3"))
DATABASE_URL = os.environ["DATABASE_URL"]

ALLOWED_TIERS = [t for t in (1, 2, 3) if t >= MAX_TIER]

mcp = FastMCP(
    f"conspiracy-wiki-tier-{MAX_TIER}plus",
    host="0.0.0.0",
    port=int(os.environ.get("PORT", "8000")),
)


def _conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


@mcp.tool()
def list_theories(category: str = "", limit: int = 50) -> list[dict]:
    """List conspiracy theories visible at this server's access tier."""
    q = "SELECT id, title, summary, tier, category FROM theories WHERE tier = ANY(%s)"
    params = [ALLOWED_TIERS]
    if category:
        q += " AND category = %s"
        params.append(category)
    q += " ORDER BY id LIMIT %s"
    params.append(limit)
    with _conn() as c, c.cursor() as cur:
        cur.execute(q, params)
        return [dict(r) for r in cur.fetchall()]


@mcp.tool()
def search_theories(query: str, limit: int = 20) -> list[dict]:
    """Full-text search within this server's allowed tiers."""
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, summary, tier, category
            FROM theories
            WHERE search_vector @@ plainto_tsquery('english', %s)
              AND tier = ANY(%s)
            LIMIT %s
            """,
            (query, ALLOWED_TIERS, limit),
        )
        return [dict(r) for r in cur.fetchall()]


@mcp.tool()
def get_theory(theory_id: int) -> dict:
    """Get one theory by id, if within this server's allowed tiers."""
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT id, title, summary, tier, category FROM theories WHERE id = %s AND tier = ANY(%s)",
            (theory_id, ALLOWED_TIERS),
        )
        row = cur.fetchone()
    if not row:
        return {"error": f"No theory with id={theory_id} accessible at this tier (allowed: {ALLOWED_TIERS})"}
    return dict(row)


@mcp.tool()
def tier_info() -> dict:
    """Report which tiers this MCP deployment can access."""
    return {"max_tier_env": MAX_TIER, "allowed_tiers": ALLOWED_TIERS}


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
