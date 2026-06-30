"""Brave Search API client.

Free tier: https://brave.com/search/api/  (the README explains setup).
"""

from __future__ import annotations

import time

import requests

BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class SearchError(RuntimeError):
    pass


def web_search(query: str, api_key: str, count: int = 10,
               user_agent: str = "AtticMooseOutreach/1.0") -> list[dict]:
    """Run one web search. Returns a list of {title, url, description}."""
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": api_key,
        "User-Agent": user_agent,
    }
    params = {"q": query, "count": min(count, 20)}
    try:
        resp = requests.get(BRAVE_ENDPOINT, headers=headers, params=params, timeout=20)
    except requests.RequestException as e:
        raise SearchError(f"Search request failed: {e}") from e

    if resp.status_code == 401:
        raise SearchError("Brave API rejected the key (401). Check search.brave_api_key in config.yaml.")
    if resp.status_code == 429:
        # Free tier is rate-limited; back off and let caller retry the next query.
        time.sleep(2.0)
        raise SearchError("Brave API rate limit hit (429). Slow down or upgrade the plan.")
    if resp.status_code != 200:
        raise SearchError(f"Brave API returned HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    results = []
    for item in (data.get("web", {}) or {}).get("results", []) or []:
        url = item.get("url")
        if not url:
            continue
        results.append({
            "title": item.get("title", ""),
            "url": url,
            "description": item.get("description", ""),
        })
    return results
