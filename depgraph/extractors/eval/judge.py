"""Judgment-mode package writer.

Produces a stable Markdown artifact (source + emitted nodes + a fixed
prompt) for a Claude Code session to review. No SDK calls.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from extractors.eval.harness import load_case, _run_extractor, _collect_node_ids


PROMPT = """## Judgment prompt

Read the source tree above and the extractor's emitted nodes. List:

1. **Missed dependencies** — nodes/edges a reviewer would expect that
   the extractor did not produce. For each: severity (low/med/high),
   one-line description, suggested detector or extractor change.
2. **False positives** — emitted nodes that don't correspond to real
   constructs in the source. Same fields.
3. **Overall verdict** — one of: clean / acceptable-with-gaps / needs-work.

Save your judgment to `judgments/<YYYY-MM-DD>.md` (sibling of this file).
"""


def write_judgment_package(case_dir: Path) -> Path:
    case = load_case(case_dir)
    out_dir = case_dir / "judgments"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / "pending.md"

    with tempfile.TemporaryDirectory() as tmp:
        data = Path(tmp)
        _run_extractor(case, repo_key="r", data_dir=data)
        emitted = _collect_node_ids(data)
        node_files: list[dict] = []
        nodes_dir = data / "nodes"
        if nodes_dir.exists():
            for sub in nodes_dir.iterdir():
                for f in sub.glob("*.json"):
                    node_files.append(json.loads(f.read_text()))

    lines = [
        f"# Judgment package: {case_dir.name}", "",
        f"Language: {case.language}",
        f"Detectors: {', '.join(case.detectors) or '(none)'}", "",
        "## Source",
        "",
    ]
    for src in sorted((case_dir / "source").rglob("*")):
        if src.is_file():
            rel = src.relative_to(case_dir / "source").as_posix()
            lines += [f"### `{rel}`", "", "```", src.read_text(), "```", ""]
    lines += [
        "## Emitted nodes",
        "",
        "```json",
        json.dumps(node_files, indent=2, sort_keys=True),
        "```",
        "",
        PROMPT,
    ]
    out.write_text("\n".join(lines))
    return out
