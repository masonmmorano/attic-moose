"""Polite web fetching: respects robots.txt and rate-limits per domain."""

from __future__ import annotations

import time
import urllib.robotparser
from urllib.parse import urlparse

import requests


class PoliteFetcher:
    """Fetches pages while obeying robots.txt and a per-domain delay."""

    def __init__(self, user_agent: str, delay_seconds: float = 2.0,
                 respect_robots: bool = True):
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.respect_robots = respect_robots
        self._last_hit: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _robots_for(self, base: str) -> urllib.robotparser.RobotFileParser | None:
        if base in self._robots:
            return self._robots[base]
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{base}/robots.txt")
        try:
            rp.read()
        except Exception:
            # If robots.txt can't be read, be conservative: treat as allow,
            # but we still rate-limit. (Most sites without robots allow all.)
            rp = None
        self._robots[base] = rp
        return rp

    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        rp = self._robots_for(base)
        if rp is None:
            return True
        try:
            return rp.can_fetch(self.user_agent, url)
        except Exception:
            return True

    def _throttle(self, netloc: str) -> None:
        last = self._last_hit.get(netloc, 0.0)
        wait = self.delay_seconds - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        self._last_hit[netloc] = time.time()

    def get(self, url: str) -> str | None:
        """Return page HTML, or None if disallowed/failed/non-HTML."""
        if not self.allowed(url):
            return None
        netloc = urlparse(url).netloc
        self._throttle(netloc)
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": self.user_agent},
                timeout=20,
                allow_redirects=True,
            )
        except requests.RequestException:
            return None
        if resp.status_code != 200:
            return None
        ctype = resp.headers.get("Content-Type", "")
        if "html" not in ctype and "text" not in ctype:
            return None
        return resp.text
