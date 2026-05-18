"""#39: v2 regen archives file-orphan nodes (source file deleted) into
`_archive/` so the live corpus does not grow monotonically as source
files come and go."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _project_layout(tmp_path: Path) -> tuple[Path, Path]:
    """Create an isolated `umbrella/depgraph` data dir + an `api` repo."""
    umbrella = tmp_path / "project"
    umbrella.mkdir()
    api = tmp_path / "api"
    api.mkdir()
    return umbrella, api


def _regen(umbrella: Path, api: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, "-m", "kg.cli",
            "depgraph", "regen",
            "--data-dir", str(umbrella),
            "--repo-key", "api",
            "--repo-path", str(api),
            "--languages", "python",
        ],
        capture_output=True, text=True, timeout=60,
    )


def test_regen_archives_node_when_source_file_deleted(tmp_path):
    umbrella, api = _project_layout(tmp_path)

    # Round 1: two files, two functions.
    (api / "alive.py").write_text("def alive():\n    pass\n")
    (api / "doomed.py").write_text("def doomed():\n    pass\n")

    r1 = _regen(umbrella, api)
    assert r1.returncode == 0, f"regen 1 failed: {r1.stdout}\n{r1.stderr}"

    depgraph = umbrella / "depgraph"
    nodes = depgraph / "nodes"
    # Sanity: doomed function was extracted on first regen.
    all_files = [p for p in nodes.rglob("*.json")
                 if not p.name.startswith("_")
                 and not any(part.startswith("_") for part in p.relative_to(nodes).parts)]
    ids = []
    for f in all_files:
        try:
            ids.append(json.loads(f.read_text()).get("id"))
        except json.JSONDecodeError:
            pass
    assert any("doomed" in (i or "") for i in ids), \
        f"doomed function should have been extracted; saw {ids}"

    # Round 2: delete doomed.py, re-regen.
    (api / "doomed.py").unlink()
    r2 = _regen(umbrella, api)
    assert r2.returncode == 0, f"regen 2 failed: {r2.stdout}\n{r2.stderr}"
    assert "archive file-orphans" in r2.stdout, r2.stdout

    # Live tree no longer has the doomed node.
    live_ids = []
    for f in nodes.rglob("*.json"):
        if f.name.startswith("_") or any(p.startswith("_") for p in f.relative_to(nodes).parts):
            continue
        try:
            live_ids.append(json.loads(f.read_text()).get("id"))
        except json.JSONDecodeError:
            pass
    assert not any("doomed" in (i or "") for i in live_ids), \
        f"doomed node should have been archived; still live: {live_ids}"

    # And it landed in `_archive/` with metadata.
    archive_dir = nodes / "_archive"
    assert archive_dir.exists(), "expected _archive/ after archival"
    archived = list(archive_dir.glob("*.json"))
    assert archived, "expected at least one archived node"
    bodies = [json.loads(f.read_text()) for f in archived]
    assert any(
        "doomed" in (b.get("id") or "")
        and b.get("_archive_reason") == "source_path_missing"
        and b.get("_archived_at")
        for b in bodies
    ), f"expected doomed/source_path_missing in archive; got {bodies}"

    # _meta.json reflects the reduced live set.
    meta = json.loads((nodes / "_meta.json").read_text())
    assert meta["node_count"] == len(live_ids)


def test_regen_preserves_archive_across_runs(tmp_path):
    """The `_archive/` directory must NOT be blown away on regen."""
    umbrella, api = _project_layout(tmp_path)

    (api / "doomed.py").write_text("def doomed():\n    pass\n")
    assert _regen(umbrella, api).returncode == 0

    # Delete, regen — archive populated.
    (api / "doomed.py").unlink()
    assert _regen(umbrella, api).returncode == 0
    archive = umbrella / "depgraph" / "nodes" / "_archive"
    first_round = {p.name for p in archive.glob("*.json")}
    assert first_round

    # Another regen with no further changes — archive should still be there.
    (api / "stable.py").write_text("def stable():\n    pass\n")
    assert _regen(umbrella, api).returncode == 0
    second_round = {p.name for p in archive.glob("*.json")}
    assert first_round.issubset(second_round), (
        f"archive was clobbered: missing {first_round - second_round}"
    )
