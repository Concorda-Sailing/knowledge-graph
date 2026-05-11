#!/usr/bin/env python3
"""
post_edit_regen.py — Stop hook (or PostToolUse).

Reads the session transcript, collects the set of files touched by Edit/Write/
MultiEdit calls, and re-runs the appropriate extractor for each. Then runs
reconcile.py and surfaces any drift signals (stale dossiers, orphans,
unresolved string URLs) as additionalContext at end of turn.

Wire it up in .claude/settings.json:

  {
    "hooks": {
      "Stop": [{
        "hooks": [{
          "type": "command",
          "command": "python3 ~/concorda/depgraph/hooks/post_edit_regen.py"
        }]
      }]
    }
  }

Design notes:

  • We deliberately re-run only the *touched* files, not the whole graph,
    to keep Stop latency low. Periodic full regens are a separate cron.
  • Extractor failures surface to Claude as warnings, not blocks. A broken
    transient state during a refactor should not prevent task completion.
  • Drift signals are summarized with counts; full lists are written to
    .claude/depgraph-last-regen.txt for follow-up.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

DEPGRAPH = Path(
    os.environ.get("DEPGRAPH_DATA_DIR")
    or os.environ.get("CONCORDA_DEPGRAPH_PATH")
    or (Path.home() / "concorda" / "depgraph")
).resolve()
HOME = Path.home()


def emit(envelope: dict) -> None:
    json.dump(envelope, sys.stdout)
    sys.stdout.write("\n")
    sys.stdout.flush()


def emit_message(msg: str) -> None:
    emit({"systemMessage": msg})


def repo_for_path(abs_path: str) -> str | None:
    p = Path(abs_path).resolve()
    parts = p.parts
    home_parts = HOME.parts
    if len(parts) <= len(home_parts):
        return None
    if parts[: len(home_parts)] != home_parts:
        return None
    seg = parts[len(home_parts)]
    if seg.startswith("concorda"):
        return seg
    return None


def collect_touched_files(payload: dict) -> dict[str, list[str]]:
    """Group touched files by repo. Reads from transcript_path if provided."""
    files: dict[str, list[str]] = {}
    transcript = payload.get("transcript_path")
    if not transcript or not Path(transcript).exists():
        return files
    seen: set[str] = set()
    for line in Path(transcript).read_text().splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        # Look for tool_use entries with edit/write
        msg = rec.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name", "")
            if name not in ("Edit", "Write", "MultiEdit"):
                continue
            inp = block.get("input") or {}
            paths = []
            if name in ("Edit", "Write"):
                if inp.get("file_path"):
                    paths.append(inp["file_path"])
            elif name == "MultiEdit":
                if inp.get("file_path"):
                    paths.append(inp["file_path"])
                for e in inp.get("edits") or []:
                    if e.get("file_path"):
                        paths.append(e["file_path"])
            for p in paths:
                if p in seen:
                    continue
                seen.add(p)
                repo = repo_for_path(p)
                if not repo:
                    continue
                files.setdefault(repo, []).append(p)
    return files


def run_extractor(repo: str, files: list[str]) -> tuple[int, str]:
    """Map repo → extractor and run it. Return (exit_code, summary_line)."""
    if repo == "concorda-api":
        cmd = ["python3", str(DEPGRAPH / "extractors" / "extract_api.py")]
        # extract_api currently runs over the whole app; --only narrows output
        for f in files:
            cmd += ["--only", f]
    elif repo == "concorda-web":
        cmd = ["npx", "tsx", str(DEPGRAPH / "extractors" / "extract_web.ts")]
    elif repo == "concorda-expo":
        cmd = ["npx", "tsx", str(DEPGRAPH / "extractors" / "extract_expo.ts")]
    elif repo == "concorda-test":
        cmd = ["npx", "tsx", str(DEPGRAPH / "extractors" / "extract_tests.ts")]
    else:
        return 0, f"{repo}: no extractor"
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    summary = (proc.stdout or "").strip().splitlines()
    last = summary[-1] if summary else ""
    if proc.returncode != 0:
        last = f"FAILED: {proc.stderr.strip()[:200]}"
    return proc.returncode, f"{repo}: {last}"


def run_reconcile() -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(DEPGRAPH / "extractors" / "reconcile.py")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc.returncode, (proc.stdout or "").strip()


def sync_memory_mirror() -> tuple[bool, str]:
    """Mirror canonical memories into concorda/memory/ so they survive a
    ~/.claude/ wipe. Best-effort: never fails the Stop hook."""
    canonical = Path.home() / ".claude" / "projects" / "-home-lgreenlee" / "memory"
    if not canonical.exists():
        return False, "memory: canonical dir missing"
    proc = subprocess.run(
        [sys.executable, str(DEPGRAPH / "bin" / "depgraph"), "memory-sync"],
        capture_output=True, text=True, timeout=30,
    )
    line = (proc.stdout or "").strip().splitlines()
    return proc.returncode == 0, (line[0] if line else "memory-sync produced no output")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    files = collect_touched_files(payload)

    # Always sync the memory mirror — regardless of whether any tracked file
    # was touched. Memory writes land in ~/.claude/, not concorda-*, so the
    # repo-touch check below would otherwise skip them.
    mem_ok, mem_summary = sync_memory_mirror()

    if not files:
        if mem_ok and "wrote" in mem_summary:
            emit_message(f"## 🗒  memory mirror\n\n{mem_summary}")
        return 0

    summaries: list[str] = []
    any_failed = False
    for repo, paths in files.items():
        rc, summary = run_extractor(repo, paths)
        summaries.append(summary)
        if rc != 0:
            any_failed = True

    rc, recon = run_reconcile()
    if rc != 0:
        any_failed = True

    msg_lines = ["## 🔁 depgraph regen", ""]
    msg_lines.extend(f"- {s}" for s in summaries)
    msg_lines.append("")
    msg_lines.append("**Reconcile:**")
    msg_lines.append("```")
    msg_lines.append(recon[:2000])
    msg_lines.append("```")
    if any_failed:
        msg_lines.insert(1, "⚠ One or more extractor steps failed — graph may be partial.")
    if mem_ok and "wrote" in mem_summary:
        msg_lines.append("")
        msg_lines.append(f"_memory mirror: {mem_summary}_")

    emit_message("\n".join(msg_lines))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        emit_message(f"⚠ depgraph post-edit hook crashed: {type(e).__name__}: {e}")
        sys.exit(0)
