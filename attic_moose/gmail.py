"""OPTIONAL Gmail API scaffold.

This is intentionally NOT wired into normal use. It's here so that, when you're
ready, turning on "create real Gmail drafts" (or sending) is a small step rather
than a rewrite.

To enable later:
  1. pip install google-api-python-client google-auth-oauthlib
  2. In Google Cloud Console, enable the Gmail API and download an OAuth client
     secret as gmail_credentials.json (placed in this folder).
  3. Run:  python -m attic_moose draft --gmail-drafts
     The first run opens a browser to authorize; a token is cached locally.

Scopes:
  - gmail.compose  -> create drafts (recommended; cannot send on its own)
  - gmail.send     -> actually send (only switch to this once you're confident)

We default to the *drafts* scope so the tool can never blast emails by accident.
"""

from __future__ import annotations

import base64
from email.message import EmailMessage
from pathlib import Path

# Drafts-only by default. Do not widen this without a deliberate decision.
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

CREDENTIALS_FILE = "gmail_credentials.json"
TOKEN_FILE = "gmail_token.json"


def _require_libs():
    try:
        from google.auth.transport.requests import Request  # noqa: F401
        from google.oauth2.credentials import Credentials  # noqa: F401
        from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401
        from googleapiclient.discovery import build  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "Gmail support needs extra packages. Run:\n"
            "  pip install google-api-python-client google-auth-oauthlib"
        ) from e


def get_service():
    """Authorize (drafts scope) and return a Gmail API service object."""
    _require_libs()
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if Path(TOKEN_FILE).exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(CREDENTIALS_FILE).exists():
                raise RuntimeError(
                    f"Missing {CREDENTIALS_FILE}. See the instructions at the top "
                    "of gmail.py to create one in Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        Path(TOKEN_FILE).write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def create_draft(service, msg: EmailMessage) -> str:
    """Create a Gmail draft from an EmailMessage. Returns the draft id."""
    raw = base64.urlsafe_b64encode(bytes(msg)).decode()
    draft = service.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}
    ).execute()
    return draft.get("id", "")
