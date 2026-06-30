"""Load and validate config.yaml."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    book: dict
    sender: dict
    search: dict
    audiences: list[str]
    regions: list[str] = field(default_factory=lambda: [""])

    @property
    def brave_api_key(self) -> str:
        return self.search.get("brave_api_key", "")

    @property
    def delay_seconds(self) -> float:
        return float(self.search.get("delay_seconds", 2.0))

    @property
    def user_agent(self) -> str:
        return self.search.get("user_agent", "AtticMooseOutreach/1.0")

    @property
    def respect_robots(self) -> bool:
        return bool(self.search.get("respect_robots", True))

    @property
    def results_per_query(self) -> int:
        return int(self.search.get("results_per_query", 10))


def _require(d: dict, key: str, where: str, errors: list[str]) -> None:
    value = d.get(key)
    if not value or (isinstance(value, str) and value.strip().startswith("PASTE")):
        errors.append(f"  - {where}.{key} is missing or not filled in")


def load_config(path: str = "config.yaml") -> Config:
    """Load config.yaml, exit with a friendly message if anything is wrong."""
    p = Path(path)
    if not p.exists():
        sys.exit(
            f"Could not find '{path}'.\n"
            "Copy config.example.yaml to config.yaml and fill it in first.\n"
            "(See the README, step 3.)"
        )

    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    book = data.get("book", {}) or {}
    sender = data.get("sender", {}) or {}
    search = data.get("search", {}) or {}

    errors: list[str] = []
    _require(book, "title", "book", errors)
    _require(book, "author", "book", errors)
    _require(book, "link", "book", errors)
    _require(sender, "reply_to", "sender", errors)
    _require(sender, "mailing_address", "sender", errors)
    _require(search, "brave_api_key", "search", errors)

    if errors:
        sys.exit(
            "Your config.yaml is missing some required values:\n"
            + "\n".join(errors)
            + "\n\nOpen config.yaml, fill those in, and run again."
        )

    audiences = data.get("audiences") or []
    if not audiences:
        sys.exit("No audiences selected in config.yaml. Add at least one under 'audiences:'.")

    regions = data.get("regions") or [""]
    return Config(book=book, sender=sender, search=search,
                  audiences=list(audiences), regions=list(regions))
