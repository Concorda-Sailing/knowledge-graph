"""Tests for event service functions."""
from ..services.events import create_event_service, list_events_service


def test_create_event_service_returns_slug():
    result = create_event_service("Test Event", "desc", "2026-01-01", 1)
    assert result.get("slug") is not None


def test_list_events_service_returns_list():
    result = list_events_service()
    assert isinstance(result, list)
