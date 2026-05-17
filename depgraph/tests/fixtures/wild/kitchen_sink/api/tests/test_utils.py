"""Tests for utility functions."""
from ..utils.format import format_date, build_event_url
from ..utils.slug import slugify
from ..utils.validate import validate_email


def test_format_date_strips_time():
    result = format_date("2026-01-01T12:00:00")
    assert "T" not in result


def test_slugify_lowercases():
    result = slugify("Hello World")
    assert result == "hello-world"
