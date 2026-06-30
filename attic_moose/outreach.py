"""Turn contacts + templates into personalized email drafts (.eml files).

Drafts-first by design: nothing is sent. You open each .eml in your mail
client, review it, and send. (See gmail.py for the optional API path.)
"""

from __future__ import annotations

import re
from email.message import EmailMessage
from pathlib import Path

from .config import Config
from .storage import OUTPUT_DIR

TEMPLATE_DIR = Path("templates")

# Legally required footer (CAN-SPAM): identify yourself, give a postal address,
# and an easy way to opt out.
FOOTER = (
    "\n\n---\n"
    "You received this because your contact info is publicly listed in relation "
    "to children's books or education. If you'd rather not hear from me, just "
    "reply with \"unsubscribe\" and I won't contact you again.\n"
    "{author} — {mailing_address}\n"
)


def _render(template: str, fields: dict) -> str:
    """Replace {placeholders}. Unknown placeholders are left intact (visible)."""
    def repl(m: re.Match) -> str:
        key = m.group(1)
        return str(fields.get(key, m.group(0)))
    return re.sub(r"\{(\w+)\}", repl, template)


def load_template(audience: str) -> tuple[str, str]:
    """Return (subject, body) from templates/<audience>.txt.

    Template format: first line is 'Subject: ...', rest is the body.
    Falls back to templates/default.txt.
    """
    path = TEMPLATE_DIR / f"{audience}.txt"
    if not path.exists():
        path = TEMPLATE_DIR / "default.txt"
    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    subject = "A children's book I'd love your thoughts on"
    body_start = 0
    if lines and lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        body_start = 1
    body = "\n".join(lines[body_start:]).strip()
    return subject, body


def build_fields(cfg: Config, contact) -> dict:
    name = (contact["name"] or "").strip() or "there"
    return {
        "name": name,
        "book_title": cfg.book.get("title", ""),
        "author": cfg.book.get("author", ""),
        "link": cfg.book.get("link", ""),
        "blurb": (cfg.book.get("blurb", "") or "").strip(),
        "org": (contact["org"] or "").strip(),
        "mailing_address": cfg.sender.get("mailing_address", ""),
        "reply_to": cfg.sender.get("reply_to", ""),
    }


def write_draft(cfg: Config, contact) -> Path:
    """Create one .eml draft for a contact. Returns the file path."""
    subject_tpl, body_tpl = load_template(contact["audience"])
    fields = build_fields(cfg, contact)

    subject = _render(subject_tpl, fields)
    body = _render(body_tpl, fields) + _render(FOOTER, fields)

    msg = EmailMessage()
    msg["To"] = contact["email"]
    msg["From"] = cfg.sender.get("reply_to", "")
    msg["Reply-To"] = cfg.sender.get("reply_to", "")
    msg["Subject"] = subject
    msg.set_content(body)

    drafts_dir = OUTPUT_DIR / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", contact["email"])
    out = drafts_dir / f"{contact['audience']}__{safe}.eml"
    out.write_bytes(bytes(msg))
    return out
