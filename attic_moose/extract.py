"""Pull contact info (emails + a best-guess name/org) from a fetched page."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

# Reasonable email matcher. Not RFC-perfect on purpose — we want common, real
# addresses, not edge cases.
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

# Addresses that are almost never a real human contact we want.
JUNK_LOCALPARTS = {
    "noreply", "no-reply", "donotreply", "postmaster", "abuse",
    "mailer-daemon", "webmaster", "root",
}
JUNK_DOMAINS = {
    "example.com", "example.org", "domain.com", "email.com", "yourdomain.com",
    "sentry.io", "wixpress.com", "schema.org", "w3.org",
}
# File-extension false positives like "logo@2x.png"
IMAGE_EXT_RE = re.compile(r"\.(png|jpe?g|gif|svg|webp|css|js)$", re.IGNORECASE)


def _clean_emails(raw: set[str]) -> list[str]:
    out: list[str] = []
    for e in raw:
        e = e.strip().strip(".").lower()
        if IMAGE_EXT_RE.search(e):
            continue
        local, _, domain = e.partition("@")
        if not domain or "." not in domain:
            continue
        if local in JUNK_LOCALPARTS:
            continue
        if domain in JUNK_DOMAINS:
            continue
        out.append(e)
    # Stable, de-duplicated
    seen: set[str] = set()
    result = []
    for e in out:
        if e not in seen:
            seen.add(e)
            result.append(e)
    return result


def extract_contacts(html: str) -> dict:
    """Return {'emails': [...], 'title': str, 'org': str}."""
    soup = BeautifulSoup(html, "html.parser")

    # Emails from visible text + mailto links.
    text = soup.get_text(" ", strip=True)
    found: set[str] = set(EMAIL_RE.findall(text))
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            addr = href[7:].split("?")[0]
            if addr:
                found.add(addr)

    emails = _clean_emails(found)

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    org = ""
    og = soup.find("meta", attrs={"property": "og:site_name"})
    if og and og.get("content"):
        org = og["content"].strip()

    return {"emails": emails, "title": title[:200], "org": org[:120]}
