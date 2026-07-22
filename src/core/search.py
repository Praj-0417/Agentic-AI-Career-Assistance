"""
src/core/search.py
─────────────────────────────────────────────────────────────────────────────
Search Tool Factory — single responsibility: build and return a search tool.

Tries Google Search (MCP/API) first, falls back to DuckDuckGo automatically.
All nodes call `get_search_tool()` — never import search libraries directly.
"""

from __future__ import annotations

import os
from typing import Callable

from dotenv import load_dotenv

load_dotenv()


# ── Search result type ───────────────────────────────────────────────────────

class SearchTool:
    """Thin wrapper so nodes can call `tool.func(query)` uniformly."""

    def __init__(self, name: str, func: Callable[[str], str]):
        self.name = name
        self.func = func

    def __repr__(self) -> str:
        return f"<SearchTool name={self.name!r}>"


# ── Google Custom Search ─────────────────────────────────────────────────────

def _google_search(query: str, num_results: int = 5) -> str:
    """
    Call Google Custom Search API (CSE).
    Requires GOOGLE_API_KEY and GOOGLE_CSE_ID in environment.
    Returns formatted string of results.
    """
    import requests as _req

    api_key = os.getenv("GOOGLE_API_KEY", "")
    cse_id  = os.getenv("GOOGLE_CSE_ID", "")

    if not api_key or not cse_id:
        raise EnvironmentError("GOOGLE_API_KEY or GOOGLE_CSE_ID not set")

    resp = _req.get(
        "https://www.googleapis.com/customsearch/v1",
        params={"key": api_key, "cx": cse_id, "q": query, "num": num_results},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    items = data.get("items", [])
    if not items:
        return f"No Google results found for: {query}"

    lines = []
    for item in items:
        title   = item.get("title", "")
        link    = item.get("link", "")
        snippet = item.get("snippet", "")
        lines.append(f"**{title}**\n{snippet}\n{link}")

    return "\n\n".join(lines)


# ── DuckDuckGo fallback ──────────────────────────────────────────────────────

def _duckduckgo_search(query: str) -> str:
    """Fallback search using DuckDuckGo (no API key required)."""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        ddg = DuckDuckGoSearchRun()
        return ddg.run(query)
    except Exception as exc:
        return f"Search unavailable: {exc}"


# ── Public factory ───────────────────────────────────────────────────────────

def get_search_tool() -> SearchTool:
    """
    Return a `SearchTool` using the best available search backend.

    Priority:
    1. Google Custom Search API (if GOOGLE_API_KEY + GOOGLE_CSE_ID are set)
    2. DuckDuckGo (always available, no key needed)
    """
    google_key = os.getenv("GOOGLE_API_KEY", "").strip()
    google_cse = os.getenv("GOOGLE_CSE_ID", "").strip()

    if google_key and google_cse:
        print("[search] Using Google Custom Search API")
        return SearchTool(name="google_search", func=_google_search)

    print("[search] Google keys not set — using DuckDuckGo fallback")
    return SearchTool(name="duckduckgo_search", func=_duckduckgo_search)
