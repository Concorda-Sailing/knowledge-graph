#!/usr/bin/env python3
"""
post_edit_telemetry.py — Claude Code Stop hook for depgraph telemetry.

At session end, scans the session transcript for mentions of node ids
(or distinctive titles) that were injected during the session, and
writes acknowledgment events to telemetry/acknowledgments.jsonl.
Combined with the injection log written by pre_edit_inject.py, this
lets us answer: "is the depgraph dependent context actually being
read, or just shouted into the void?"

Acknowledgment is a soft signal — the LLM mentioning a node by name
does not prove the dependent context influenced the decision, only
that it was read and processed. The opposite (node injected, never
mentioned) is the stronger signal: dossier prose worth re-reviewing.

Mirrors the logigraph telemetry hook deliberately. Both feed the same
"does the substrate actually change behavior" question.

Failure modes:
  - No transcript_path in payload → silent exit 0.
  - Transcript file missing → silent exit 0.
  - Telemetry write failure → silent swallow (telemetry must not block).
  - Any unhandled exception → silent exit 0 (Stop hooks must never
    error out and break session close).

Time window: scans injections from the last 6 hours (rough proxy for
"current session"). Could be tightened with a session_id from the
harness if/when one becomes available.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent
_FRAMEWORK_ROOT = TOOL_ROOT.parent  # ~/tools/knowledge-graph
sys.path.insert(0, str(_FRAMEWORK_ROOT))
from depgraph.lib.config import resolve_data_dir  # noqa: E402
from depgraph.lib.edges import (  # noqa: E402
    ACKNOWLEDGMENTS_LOG_FILENAME,
    INJECTIONS_LOG_FILENAME,
)
from kg.shared.env import DEPGRAPH_DATA_DIR  # noqa: E402

DEPGRAPH = resolve_data_dir(DEPGRAPH_DATA_DIR)
TELEMETRY_DIR = DEPGRAPH / "telemetry"
INJECTIONS_LOG = TELEMETRY_DIR / INJECTIONS_LOG_FILENAME
ACKS_LOG = TELEMETRY_DIR / ACKNOWLEDGMENTS_LOG_FILENAME
NODES_DIR = DEPGRAPH / "nodes"

SESSION_WINDOW_HOURS = 6
# Title-match threshold: shorter symbol names (Person, Event, Item) are too
# common in prose to be reliable. Require at least this many characters AND a
# capital letter to count a title-only match.
TITLE_MIN_LEN = 8


def _silent_exit(rc: int = 0) -> None:
    sys.exit(rc)


def _load_recent_injections() -> list[dict]:
    if not INJECTIONS_LOG.exists():
        return []
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=SESSION_WINDOW_HOURS)
    out: list[dict] = []
    try:
        with INJECTIONS_LOG.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts_str = ev.get("ts")
                if not ts_str:
                    continue
                try:
                    ts = dt.datetime.fromisoformat(ts_str)
                except ValueError:
                    continue
                if ts >= cutoff:
                    out.append(ev)
    except OSError:
        return []
    return out


def _node_titles_for(node_ids: set[str]) -> dict[str, str]:
    """Return {node_id: title} for the given ids by scanning node JSON files.
    We walk all node files rather than guessing paths because depgraph nodes
    live in many subdirectories (models, services, components, ...)."""
    titles: dict[str, str] = {}
    if not NODES_DIR.exists():
        return titles
    needed = set(node_ids)
    for path in NODES_DIR.rglob("*.json"):
        if not needed:
            break
        # Skip index/meta and archived nodes.
        if path.name.startswith("_") or any(p.startswith("_") for p in path.relative_to(NODES_DIR).parts):
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = data.get("id")
        if nid in needed and data.get("title"):
            titles[nid] = data["title"]
            needed.discard(nid)
    return titles


def _read_transcript(transcript_path: str) -> str:
    if not transcript_path:
        return ""
    p = Path(transcript_path)
    if not p.exists():
        return ""
    parts: list[str] = []
    try:
        with p.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = msg.get("message", {}).get("content") or msg.get("content")
                role = (msg.get("message", {}).get("role") or msg.get("role") or "").lower()
                if role and role != "assistant":
                    continue
                if isinstance(content, str):
                    parts.append(content)
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") in ("text", "thinking"):
                            t = block.get("text") or block.get("thinking") or ""
                            if t:
                                parts.append(t)
    except OSError:
        return ""
    return "\n".join(parts)


def _record_acknowledgment(node_id: str, matched_phrase: str) -> None:
    try:
        TELEMETRY_DIR.mkdir(parents=True, exist_ok=True)
        ts = dt.datetime.now(dt.timezone.utc).isoformat()
        with ACKS_LOG.open("a") as f:
            f.write(json.dumps({
                "ts": ts,
                "kind": "acknowledgment",
                "node_id": node_id,
                "matched_phrase": matched_phrase[:120],
            }) + "\n")
    except OSError:
        pass


def _title_match(title: str, transcript: str) -> bool:
    """Word-boundary match on a title, gated by the length + capitalization
    heuristic that filters out generic prose collisions."""
    if not title or len(title) < TITLE_MIN_LEN:
        return False
    if not any(c.isupper() for c in title):
        return False
    return re.search(rf"\b{re.escape(title)}\b", transcript) is not None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        _silent_exit(0)

    transcript_path = payload.get("transcript_path", "")
    transcript = _read_transcript(transcript_path)
    if not transcript:
        _silent_exit(0)

    injections = _load_recent_injections()
    if not injections:
        _silent_exit(0)

    candidate_node_ids = {ev.get("node_id") for ev in injections if ev.get("node_id")}
    titles = _node_titles_for(candidate_node_ids)

    acknowledged: set[str] = set()
    for nid in candidate_node_ids:
        if nid in transcript:
            _record_acknowledgment(nid, nid)
            acknowledged.add(nid)
            continue
        title = titles.get(nid, "")
        if _title_match(title, transcript):
            _record_acknowledgment(nid, title)
            acknowledged.add(nid)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
