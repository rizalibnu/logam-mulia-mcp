"""
MCP Server — Logam Mulia API

Exposes Indonesian gold (logam mulia) price data from various sources
as MCP tools.

Base URL configurable via LOGAM_MULIA_BASE_URL env var.
Transport: stdio (default) or sse via MCP_TRANSPORT=sse.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

__version__ = "1.2.0"

# ── Configuration ──────────────────────────────────────────────────────────

BASE_URL = os.environ.get(
    "LOGAM_MULIA_BASE_URL",
    "https://logam-mulia-api.iamutaki.workers.dev",
)
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
HTTP_TIMEOUT = int(os.environ.get("HTTP_TIMEOUT", "30"))

# ── MCP Server ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    "logam-mulia",
    instructions=(
        "Indonesian gold (logam mulia) price data from dynamic sources. "
        "Get current prices, history, and news. "
        "Configure LOGAM_MULIA_BASE_URL env to change API base."
    ),
    website_url="https://github.com/rizalibnu/logam-mulia-mcp",
)

# ── HTTP Client (lazy) ─────────────────────────────────────────────────────

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=HTTP_TIMEOUT,
            headers={"User-Agent": "logam-mulia-mcp/1.0"},
        )
    return _client


async def _api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET from the Logam Mulia API. Returns parsed JSON."""
    client = get_client()
    resp = await client.get(path, params=params)
    resp.raise_for_status()
    return resp.json()


# ── Dynamic source list (live from API, cached 5 min) ─────────────────────

_sources_cache: tuple[float, list[dict[str, str]]] | None = None
_SOURCE_CACHE_TTL = 300  # 5 minutes


async def _get_sources() -> list[dict[str, str]]:
    """Fetch available price sources from the API, cached for 5 min."""
    global _sources_cache  # noqa: PLW0603

    now = time.time()
    if _sources_cache is not None and (now - _sources_cache[0]) < _SOURCE_CACHE_TTL:
        return _sources_cache[1]

    try:
        data = await _api_get("/api/prices")
        if not data.get("data"):
            return _sources_cache[1] if _sources_cache else []

        sources = [
            {"id": s["name"], "name": s.get("displayName", s["name"])}
            for s in data["data"]
            if s.get("name")
        ]
        _sources_cache = (now, sources)
        return sources
    except Exception:  # noqa: BLE001
        # On failure, return stale cache if available
        return _sources_cache[1] if _sources_cache else []


# ── Tools ──────────────────────────────────────────────────────────────────


@mcp.tool()
async def get_price(
    source: str,
    refresh: bool = False,
) -> str:
    """Get latest gold price from a specific source.

    Args:
        source: Price source id (e.g. 'anekalogam', 'pegadaian', 'galeri24').
               Use list_sources() to see all.
        refresh: If True, bypass cache and force fresh scrape.
    """
    params: dict[str, Any] = {}
    if refresh:
        params["refresh"] = "true"

    try:
        data = await _api_get(f"/api/prices/{source}", params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Source '{source}' not found. Use list_sources() to see available sources."
        return f"API error: {e.response.status_code} — {e.response.text}"
    except httpx.RequestError as e:
        return f"Connection error: {e}"

    if not data.get("success"):
        return f"API returned error: {data}"

    prices = data.get("data", [])
    if not prices:
        return f"No price data for source '{source}'."

    lines = [f"Source: {p.get('displayName', source)} ({p.get('source', '')})" for p in prices]
    for p in prices:
        lines.append(
            f"  - {p.get('material', '?')}/{p.get('materialType', '?')} "
            f"{p.get('weight')}{p.get('weightUnit', 'gr')}: "
            f"Sell Rp{p.get('sellPrice', '?'):,} | "
            f"Buyback Rp{p.get('buybackPrice', '?'):,}"
        )

    lines.append(f"Recorded: {prices[0].get('recordedDate', '?')}")
    lines.append(f"Cached: {data.get('cached', False)}")
    lines.append(f"Timestamp: {data.get('timestamp', '?')}")

    return "\n".join(lines)


@mcp.tool()
async def get_price_history(
    source: str,
    page: int = 1,
    length: int = 20,
    weight: int | None = None,
    material: str | None = None,
    material_type: str | None = None,
) -> str:
    """Get historical price data from a source.

    Args:
        source: Price source id.
        page: Page number (default 1).
        length: Items per page, max 1000 (default 20).
        weight: Filter by weight in grams (e.g. 1, 5, 10).
        material: Filter by material type (e.g. 'gold', 'silver').
        material_type: Filter by material type name (e.g. 'ANTAM', 'UBS', 'GALERI 24').
    """
    params: dict[str, Any] = {"page": page, "length": min(length, 1000)}
    if weight is not None:
        params["weight"] = weight
    if material:
        params["material"] = material
    if material_type:
        params["materialType"] = material_type

    try:
        data = await _api_get(f"/api/prices/{source}/history", params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return f"Source '{source}' not found or has no history endpoint."
        return f"API error: {e.response.status_code}"
    except httpx.RequestError as e:
        return f"Connection error: {e}"

    if not data.get("success"):
        return f"API returned error: {data}"

    prices = data.get("data", [])
    if not prices:
        return f"No history for source '{source}' with those filters."

    lines = [
        f"History: {source} (page {page}, {len(prices)} items)",
        "",
    ]
    for p in prices:
        lines.append(
            f"  {p.get('recordedDate', '?')} "
            f"| {p.get('materialType', '?')} "
            f"{p.get('weight')}{p.get('weightUnit', 'gr')} "
            f"| Sell Rp{p.get('sellPrice', '?'):,} "
            f"| Buyback Rp{p.get('buybackPrice', '?'):,}"
        )

    lines.append("")
    lines.append(f"Timestamp: {data.get('timestamp', '?')}")
    return "\n".join(lines)


@mcp.tool()
async def list_sources() -> str:
    """List all available price sources."""
    sources = await _get_sources()
    lines = [f"Available sources ({len(sources)}):", ""]
    for s in sources:
        lines.append(f"  {s['id']:25s} — {s['name']}")
    lines.append("")
    lines.append(f"Base URL: {BASE_URL}")
    return "\n".join(lines)


@mcp.tool()
async def get_news() -> str:
    """Get latest gold-related news from Investor ID."""
    try:
        data = await _api_get("/api/news/investor-id")
    except httpx.RequestError as e:
        return f"Connection error: {e}"

    if not data.get("success"):
        return f"API returned error: {data}"

    articles = data.get("data", [])
    if not articles:
        return "No news available."

    lines = [f"Latest gold news ({len(articles)} articles):", ""]
    for a in articles:
        lines.append(f"  \U0001f4f0 {a.get('title', '?')}")
        lines.append(f"     Category: {a.get('category', '?')}")
        lines.append(f"     Published: {a.get('publishedAt', '?')}")
        lines.append(f"     Summary: {a.get('summary', '?')[:200]}")
        lines.append(f"     URL: {a.get('url', '?')}")
        lines.append("")

    lines.append(f"Timestamp: {data.get('timestamp', '?')}")
    return "\n".join(lines)


@mcp.tool()
async def get_news_detail(url: str) -> str:
    """Get full detail of a news article.

    Args:
        url: The article URL from get_news() output.
    """
    try:
        data = await _api_get("/api/news/investor-id/detail", {"url": url})
    except httpx.RequestError as e:
        return f"Connection error: {e}"

    if not data.get("success"):
        return f"API returned error: {data}"

    article = data.get("data", {})
    if not article:
        return "No article detail found."

    lines = [
        f"# {article.get('title', '?')}",
        f"Author: {article.get('author', '?')}",
        f"Published: {article.get('publishedAt', '?')}",
        f"Tags: {article.get('tags', '?')}",
        "",
        article.get("content", "No content."),
    ]
    return "\n".join(lines)


@mcp.tool()
async def get_all_prices() -> str:
    """Get latest gold prices from ALL available sources at once."""
    sources = await _get_sources()
    results = []

    for source_info in sources:
        sid = source_info["id"]
        try:
            data = await _api_get(f"/api/prices/{sid}")
            if data.get("success") and data.get("data"):
                p = data["data"][0]
                results.append(
                    f"{sid:22s} | "
                    f"Sell Rp{p.get('sellPrice', '?'):>12,} | "
                    f"Buyback Rp{p.get('buybackPrice', '?'):>12,} | "
                    f"{p.get('weight')}{p.get('weightUnit', 'gr')} {p.get('materialType', '')}"
                )
            else:
                results.append(f"{sid:22s} | No data")
        except Exception as e:  # noqa: BLE001
            results.append(f"{sid:22s} | Error: {e}")

    lines = [
        "All prices (latest per source):",
        "",
        f"{'Source':22s} | {'Sell Price':>15s} | {'Buyback':>15s} | Detail",
        f"{'------':22s} | {'----------':>15s} | {'-------':>15s} | ------",
    ]
    lines.extend(results)
    return "\n".join(lines)


# ── Entrypoint ─────────────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server with configured transport."""
    mcp.run(transport=TRANSPORT)


if __name__ == "__main__":
    main()
