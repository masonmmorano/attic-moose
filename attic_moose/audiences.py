"""Audience definitions: how we search for each kind of reviewer.

Every query is aimed at PUBLIC, contact-intended pages — review policies,
staff directories, association contact pages, public business emails.
We do not target login-walled or scrape-prohibited sources.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Audience:
    key: str
    label: str
    # {region} is filled in from config; trailing space is fine.
    queries: list[str]


AUDIENCES: dict[str, Audience] = {
    "blogger": Audience(
        key="blogger",
        label="Children's book blogger",
        queries=[
            '{region} children\'s book blog "review policy" contact',
            '{region} "children\'s book reviews" blog "submit your book" contact email',
            '{region} kidlit blog "review requests" contact',
        ],
    ),
    "librarian": Audience(
        key="librarian",
        label="Librarian (youth/children's services)",
        queries=[
            '{region} public library "youth services" OR "children\'s services" staff contact email',
            '{region} library "children\'s librarian" contact directory',
            '{region} school library media specialist contact directory',
        ],
    ),
    "teacher": Audience(
        key="teacher",
        label="Teacher / elementary educator",
        queries=[
            '{region} elementary school staff directory teacher email',
            '{region} "early childhood" educator association contact',
            '{region} reading specialist elementary contact directory',
        ],
    ),
    "therapist": Audience(
        key="therapist",
        label="Therapist (works with children)",
        queries=[
            '{region} child therapist practice contact email "play therapy"',
            '{region} pediatric counseling practice contact',
            '{region} family therapist children contact directory',
        ],
    ),
    "child_psychologist": Audience(
        key="child_psychologist",
        label="Child psychologist",
        queries=[
            '{region} child psychologist practice contact email',
            '{region} pediatric psychology practice contact',
            '{region} developmental psychologist children contact',
        ],
    ),
    "influencer": Audience(
        key="influencer",
        label="Children's-book influencer / creator",
        queries=[
            '{region} kidlit bookstagram "business inquiries" contact email',
            '{region} children\'s book influencer "for business" contact email',
            '{region} "children\'s books" content creator media kit contact',
        ],
    ),
    "homeschool": Audience(
        key="homeschool",
        label="Homeschool group / association",
        queries=[
            '{region} homeschool association contact email',
            '{region} homeschool co-op group contact',
            '{region} homeschool curriculum reviewer contact',
        ],
    ),
}


def build_queries(audience_keys: list[str], regions: list[str]) -> list[tuple[str, str]]:
    """Return (audience_key, query_string) pairs for the selected audiences/regions."""
    pairs: list[tuple[str, str]] = []
    regions = regions or [""]
    for key in audience_keys:
        aud = AUDIENCES.get(key)
        if not aud:
            continue
        for region in regions:
            for template in aud.queries:
                q = template.replace("{region}", region.strip()).strip()
                # Collapse double spaces left when region is empty.
                q = " ".join(q.split())
                pairs.append((key, q))
    return pairs
