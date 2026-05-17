"""Date and URL formatting utilities."""


def format_date(date_str: str) -> str:
    """Format an ISO date string for display."""
    return date_str.replace("T", " ").split(".")[0]


def build_event_url(slug: str, base_url: str = "https://example.com") -> str:
    """Build a canonical event URL from its slug."""
    return f"{base_url}/events/{slug}"


def parse_iso_date(date_str: str) -> str:
    """Parse an ISO 8601 date string; return normalized form."""
    parts = date_str.split("T")
    return parts[0] if parts else date_str
