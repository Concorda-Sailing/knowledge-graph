"""Validation utilities."""
import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> bool:
    """Return True if the email looks valid."""
    return bool(_EMAIL_RE.match(email))
