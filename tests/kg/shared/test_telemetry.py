"""Tests for kg.shared.telemetry."""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pytest

from kg.shared.telemetry import load_telemetry_events


def test_load_returns_empty_when_file_missing(tmp_path: Path) -> None:
    assert load_telemetry_events(tmp_path / "missing.jsonl") == []


def test_load_returns_all_events(tmp_path: Path) -> None:
    p = tmp_path / "events.jsonl"
    p.write_text(
        '{"ts": "2026-05-16T10:00:00+00:00", "evt": "a"}\n'
        '{"ts": "2026-05-16T11:00:00+00:00", "evt": "b"}\n'
    )
    events = load_telemetry_events(p)
    assert len(events) == 2
    assert events[0]["evt"] == "a"


def test_load_filters_by_since_hours(tmp_path: Path) -> None:
    p = tmp_path / "events.jsonl"
    now = _dt.datetime.now(_dt.timezone.utc)
    old = (now - _dt.timedelta(hours=48)).isoformat()
    new = (now - _dt.timedelta(hours=1)).isoformat()
    p.write_text(
        f'{{"ts": "{old}", "evt": "old"}}\n'
        f'{{"ts": "{new}", "evt": "new"}}\n'
    )
    events = load_telemetry_events(p, since_hours=24)
    assert len(events) == 1
    assert events[0]["evt"] == "new"


def test_load_skips_blank_lines_and_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "events.jsonl"
    p.write_text(
        '\n'
        '{"ts": "2026-05-16T10:00:00+00:00", "evt": "ok"}\n'
        'not-json\n'
        '\n'
    )
    events = load_telemetry_events(p)
    assert len(events) == 1
    assert events[0]["evt"] == "ok"
