"""Attic Moose command-line interface.

Commands:
  discover   Search the web and collect contacts into contacts.db
  list       Show what's been collected (optionally export CSV)
  draft      Generate personalized .eml email drafts for review
  suppress   Add an email to the do-not-contact list
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .audiences import AUDIENCES, build_queries
from .config import load_config
from .extract import extract_contacts
from .fetch import PoliteFetcher
from .search import SearchError, web_search
from . import storage
from .outreach import write_draft


def cmd_discover(args) -> None:
    cfg = load_config(args.config)
    conn = storage.connect(args.db)
    fetcher = PoliteFetcher(cfg.user_agent, cfg.delay_seconds, cfg.respect_robots)

    queries = build_queries(cfg.audiences, cfg.regions)
    if args.limit:
        queries = queries[: args.limit]

    print(f"Running {len(queries)} searches across {len(cfg.audiences)} audience(s)...\n")
    seen_urls: set[str] = set()
    new_total = 0

    for i, (audience, query) in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {AUDIENCES[audience].label}: {query}")
        try:
            results = web_search(query, cfg.brave_api_key,
                                 count=cfg.results_per_query, user_agent=cfg.user_agent)
        except SearchError as e:
            print(f"    ! {e}")
            continue

        for r in results:
            url = r["url"]
            if url in seen_urls:
                continue
            seen_urls.add(url)
            html = fetcher.get(url)
            if not html:
                continue
            info = extract_contacts(html)
            for email in info["emails"]:
                added = storage.upsert_contact(
                    conn, email=email, audience=audience, source_url=url,
                    source_title=info["title"] or r["title"], org=info["org"],
                )
                if added:
                    new_total += 1
                    print(f"    + {email}  ({audience})")

    print(f"\nDone. {new_total} new contact(s) added.")
    out = storage.export_csv(conn)
    print(f"Full list exported to {out}")
    print("Review it before drafting — delete any contact that doesn't look right.")


def cmd_list(args) -> None:
    conn = storage.connect(args.db)
    rows = storage.contacts_by_status(conn, args.status)
    if not rows:
        print("No contacts yet. Run:  python -m attic_moose discover")
        return
    by_aud: dict[str, int] = {}
    for r in rows:
        by_aud[r["audience"]] = by_aud.get(r["audience"], 0) + 1
    print(f"{len(rows)} contact(s):")
    for aud, n in sorted(by_aud.items()):
        print(f"  {aud:20s} {n}")
    if args.export:
        out = storage.export_csv(conn)
        print(f"\nExported to {out}")


def cmd_draft(args) -> None:
    cfg = load_config(args.config)
    conn = storage.connect(args.db)
    rows = storage.contacts_by_status(conn, "new")
    if not rows:
        print("No 'new' contacts to draft. Run discover first, or check `list`.")
        return

    gmail_service = None
    if args.gmail_drafts:
        from .gmail import get_service
        gmail_service = get_service()
        print("Gmail authorized — drafts will be created in your account.\n")

    count = 0
    for r in rows:
        path = write_draft(cfg, r)
        if gmail_service is not None:
            import email as _email
            from .gmail import create_draft
            with open(path, "rb") as f:
                msg = _email.message_from_binary_file(f, _class=_email.message.EmailMessage)
            create_draft(gmail_service, msg)
        storage.mark_status(conn, r["email"], "drafted")
        count += 1

    print(f"Created {count} draft(s) in output/drafts/")
    if not args.gmail_drafts:
        print("Open each .eml in your mail client to review and send.")


def cmd_suppress(args) -> None:
    conn = storage.connect(args.db)
    storage.add_suppression(conn, args.email, reason=args.reason)
    print(f"{args.email} added to the do-not-contact list.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="attic_moose",
                                description="Compliant outreach tool for children's book reviews.")
    p.add_argument("--version", action="version", version=f"attic_moose {__version__}")
    p.add_argument("--config", default="config.yaml", help="path to config (default: config.yaml)")
    p.add_argument("--db", default=storage.DB_PATH, help="path to contacts DB")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("discover", help="search the web and collect contacts")
    d.add_argument("--limit", type=int, default=0, help="only run the first N searches (for testing)")
    d.set_defaults(func=cmd_discover)

    ls = sub.add_parser("list", help="show collected contacts")
    ls.add_argument("--status", help="filter by status (new/drafted/sent)")
    ls.add_argument("--export", action="store_true", help="also export CSV")
    ls.set_defaults(func=cmd_list)

    dr = sub.add_parser("draft", help="generate personalized email drafts")
    dr.add_argument("--gmail-drafts", action="store_true",
                    help="also create real drafts in Gmail (needs setup; see gmail.py)")
    dr.set_defaults(func=cmd_draft)

    sp = sub.add_parser("suppress", help="add an email to the do-not-contact list")
    sp.add_argument("email")
    sp.add_argument("--reason", default="manual")
    sp.set_defaults(func=cmd_suppress)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
