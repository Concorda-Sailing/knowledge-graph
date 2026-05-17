"""Slug and RSVP count utilities."""


def slugify(text: str) -> str:
    """Convert a string to a URL-safe slug."""
    return text.lower().replace(" ", "-").replace("_", "-")


def compute_rsvp_count(rsvps: list) -> int:
    """Count attending RSVPs from a list of RSVP records."""
    return sum(1 for r in rsvps if r.get("status") == "attending")
