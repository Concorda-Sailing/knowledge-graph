"""Telemetry-log helpers used by depgraph and logigraph CLIs."""
from __future__ import annotations

import json
from pathlib import Path


def load_telemetry_events(path: Path, since_hours: int | None = None) -> list[dict]:
    """Read a JSONL log; if since_hours is given, filter to events newer
    than that. Returns an empty list if the file is missing or unreadable."""
    if not path.exists():
        return []
    import datetime as _dt
    cutoff = None
    if since_hours is not None:
        cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=since_hours)
    out: list[dict] = []
    try:
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if cutoff is not None:
                    ts_str = ev.get("ts", "")
                    try:
                        ts = _dt.datetime.fromisoformat(ts_str)
                    except ValueError:
                        continue
                    if ts < cutoff:
                        continue
                out.append(ev)
    except OSError:
        return []
    return out
