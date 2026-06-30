"""SQLite storage + CSV export + suppression (unsubscribe) list."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "contacts.db"
OUTPUT_DIR = Path("output")

SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    email        TEXT PRIMARY KEY,
    name         TEXT,
    org          TEXT,
    audience     TEXT,
    source_url   TEXT,
    source_title TEXT,
    discovered_at TEXT,
    status       TEXT DEFAULT 'new'   -- new | drafted | sent | bounced
);
CREATE TABLE IF NOT EXISTS suppression (
    email      TEXT PRIMARY KEY,
    reason     TEXT,
    added_at   TEXT
);
"""


def connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_suppressed(conn: sqlite3.Connection, email: str) -> bool:
    cur = conn.execute("SELECT 1 FROM suppression WHERE email = ?", (email.lower(),))
    return cur.fetchone() is not None


def add_suppression(conn: sqlite3.Connection, email: str, reason: str = "unsubscribe") -> None:
    conn.execute(
        "INSERT OR REPLACE INTO suppression(email, reason, added_at) VALUES (?,?,?)",
        (email.lower(), reason, _now()),
    )
    conn.commit()


def upsert_contact(conn: sqlite3.Connection, *, email: str, audience: str,
                   source_url: str, source_title: str = "", name: str = "",
                   org: str = "") -> bool:
    """Insert a contact if new and not suppressed. Returns True if newly added."""
    email = email.lower()
    if is_suppressed(conn, email):
        return False
    existing = conn.execute("SELECT 1 FROM contacts WHERE email = ?", (email,)).fetchone()
    if existing:
        return False
    conn.execute(
        """INSERT INTO contacts(email, name, org, audience, source_url,
                                source_title, discovered_at, status)
           VALUES (?,?,?,?,?,?,?, 'new')""",
        (email, name, org, audience, source_url, source_title, _now()),
    )
    conn.commit()
    return True


def contacts_by_status(conn: sqlite3.Connection, status: str | None = None) -> list[sqlite3.Row]:
    if status:
        cur = conn.execute("SELECT * FROM contacts WHERE status = ? ORDER BY audience, email", (status,))
    else:
        cur = conn.execute("SELECT * FROM contacts ORDER BY audience, email")
    return cur.fetchall()


def mark_status(conn: sqlite3.Connection, email: str, status: str) -> None:
    conn.execute("UPDATE contacts SET status = ? WHERE email = ?", (status, email.lower()))
    conn.commit()


def export_csv(conn: sqlite3.Connection, path: str | None = None) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = Path(path) if path else OUTPUT_DIR / "contacts.csv"
    rows = contacts_by_status(conn)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["email", "name", "org", "audience", "source_url",
                         "source_title", "discovered_at", "status"])
        for r in rows:
            writer.writerow([r["email"], r["name"], r["org"], r["audience"],
                             r["source_url"], r["source_title"],
                             r["discovered_at"], r["status"]])
    return out
