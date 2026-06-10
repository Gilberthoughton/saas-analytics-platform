"""Small text helpers."""

import re
import secrets


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "org"


def slug_with_suffix(value: str) -> str:
    """Slug plus a short random suffix, for collision avoidance."""
    return f"{slugify(value)}-{secrets.token_hex(3)}"
