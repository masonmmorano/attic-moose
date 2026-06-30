# CLAUDE.md

Guidance for Claude Code (and contributors) working in this repository.

## What this project is

**Attic Moose** is a Python CLI that helps an author find legitimate reviewers
for a children's book and send them personalized outreach. It discovers
*public, contact-intended* contacts (review policies, staff/association
directories, public business emails), stores them, and generates personalized
email **drafts** for the author to review and send.

The primary user is **non-technical** and follows `README.md` step by step.
Optimize docs and error messages for that person: plain language, copy-paste
commands, friendly failures.

## Hard rules (do not regress these)

This tool is deliberately compliant. Keep it that way:

- **No ToS-violating scraping.** No logging into or scraping Instagram/Facebook,
  no bypassing paywalls/login walls, no CAPTCHA solving. Only public,
  contact-intended pages.
- **Respect `robots.txt` and rate limits.** `fetch.PoliteFetcher` enforces both;
  don't add fetch paths that bypass it. `respect_robots` defaults to true.
- **Drafts, not blasts.** Default behavior generates `.eml` drafts the user
  sends manually. The Gmail integration (`gmail.py`) is **drafts-only scope**
  (`gmail.compose`) on purpose — do not widen to `gmail.send` without an
  explicit, deliberate request.
- **CAN-SPAM footer is mandatory.** Every generated email includes an
  unsubscribe line + the sender's postal address (`outreach.FOOTER`). Don't
  remove it.
- **Honor the suppression list.** `storage.upsert_contact` and outreach must
  never contact a suppressed address.
- Store the **source URL** for every contact so the user can verify relevance.

If a request conflicts with these, surface the concern rather than silently
implementing it.

## Layout

```
attic_moose/            # the package (run as `python -m attic_moose`)
  __main__.py           # CLI: discover / list / draft / suppress
  config.py             # loads & validates config.yaml
  audiences.py          # audience definitions + per-audience search queries
  search.py             # Brave Search API client
  fetch.py              # robots.txt-respecting, rate-limited fetcher
  extract.py            # email extraction + junk filtering (bs4)
  storage.py            # SQLite (contacts + suppression) + CSV export
  outreach.py           # renders templates -> .eml drafts (+ CAN-SPAM footer)
  gmail.py              # OPTIONAL Gmail drafts scaffold (off by default)
templates/              # one editable email template per audience (+ default)
config.example.yaml     # copy -> config.yaml (git-ignored; holds API key)
```

Package uses a **flat (root) layout**, not `src/`, so `python -m attic_moose`
works from the repo root with no install step — important for the non-technical
user. Keep it that way.

## Conventions

- Modules start with `from __future__ import annotations` so modern type hints
  (`str | None`, `list[str]`) work on the user's older Python (3.7 seen locally).
  Keep this import when adding modules, or runtime will break on 3.7.
- New audiences: add an entry to `audiences.AUDIENCES` **and** a matching
  `templates/<key>.txt`. Templates: first line `Subject: ...`, rest is the body;
  merge fields are `{name} {book_title} {author} {link} {blurb} {org}
  {mailing_address} {reply_to}`.
- Secrets/config (`config.yaml`, `gmail_credentials.json`, `gmail_token.json`)
  and generated data (`output/`, `*.db`) are git-ignored. Never commit them.

## Running / testing

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp config.example.yaml config.yaml   # then fill in book details + Brave key
python -m attic_moose discover --limit 3   # small live test
python -m attic_moose draft
```

There's no formal test suite yet. The discovery/extraction/storage/outreach
paths have been smoke-tested offline. If you add tests, prefer offline unit
tests for `extract`, `storage`, and `outreach` (no network); gate anything that
hits Brave or the live web behind an explicit flag.

## Status

v1 complete and smoke-tested. Not yet validated against a live Brave key.
Gmail sending is intentionally not enabled (drafts-only).
