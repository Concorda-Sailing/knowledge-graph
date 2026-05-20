"""#38 sub-item G: v2 regen strips v1-era legacy fields (`dependents`,
`extracted_at`, `git_commit`) from any live node JSON still carrying them.

`write_classified` overwrites every freshly-extracted primitive without
those keys, so the strip pass is a no-op on a corpus born under v2. It
only matters when a corpus was migrated forward from the v1 reconcile.py
era, or when a partial regen leaves another repo's older nodes untouched
on disk. The v1 implementation lived in `reconcile.strip_legacy_fields`
and only ran inside the long-deprecated `_mode_a_v1_fallback` subprocess
path — wiring it into `_run_v2_pipeline` closes the gap.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _project_layout(tmp_path: Path) -> tuple[Path, Path]:
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


def _live_node_files(depgraph: Path) -> list[Path]:
    nodes = depgraph / "nodes"
    out: list[Path] = []
    for f in nodes.rglob("*.json"):
        if f.name.startswith("_") or any(
            p.startswith("_") for p in f.relative_to(nodes).parts
        ):
            continue
        out.append(f)
    return out


def test_regen_strips_legacy_dependents_field(tmp_path):
    """A node JSON carrying a v1-era `dependents` array (now hosted in
    `nodes/_index/by_target.json`) should be cleaned by the strip pass."""
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def widget():\n    return 1\n")

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    node_files = _live_node_files(depgraph)
    assert node_files, "first regen produced no live node files"

    # Simulate a corpus migrated forward from v1: inject the three legacy
    # fields onto an existing node JSON.
    target = node_files[0]
    data = json.loads(target.read_text())
    data["dependents"] = ["external::pretend.caller"]
    data["extracted_at"] = "2025-01-01T00:00:00Z"
    data["git_commit"] = "deadbeef"
    target.write_text(json.dumps(data, indent=2, sort_keys=True))

    # Re-run regen. The strip pass should remove all three keys.
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "strip legacy fields" in r.stdout

    cleaned = json.loads(target.read_text())
    assert "dependents" not in cleaned
    assert "extracted_at" not in cleaned
    assert "git_commit" not in cleaned


def test_regen_strip_legacy_is_idempotent_on_v2_native_corpus(tmp_path):
    """A corpus born under v2 carries no legacy fields, so the strip pass
    cleans zero nodes and leaves every on-disk file untouched."""
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def widget():\n    return 1\n")

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "strip legacy fields" in r.stdout

    depgraph = umbrella / "depgraph"
    legacy_keys = {"dependents", "extracted_at", "git_commit"}
    for f in _live_node_files(depgraph):
        data = json.loads(f.read_text())
        assert legacy_keys.isdisjoint(data.keys()), (
            f"freshly-written v2 node carries legacy keys: "
            f"{sorted(legacy_keys & data.keys())} on {f.name}"
        )

    # A second regen with no changes must also produce zero hits.
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "cleaned: 0" in r.stdout
