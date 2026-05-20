"""#38 sub-item E: v2 regen runs `detect_stale_dossiers` after stubbing
missing dossiers and stamps `dossier_state: "stale"` on every node whose
dossier pins a hash that no longer matches the current `structural_hash`.

v1 reconcile only printed the count; v2 persists the verdict on the node
so downstream consumers (graphui, dossier-rank, health) can read it
without re-walking the dossier corpus.
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


def _live_nodes(depgraph: Path) -> list[dict]:
    nodes = depgraph / "nodes"
    out: list[dict] = []
    for f in nodes.rglob("*.json"):
        if f.name.startswith("_") or any(
            p.startswith("_") for p in f.relative_to(nodes).parts
        ):
            continue
        try:
            out.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            pass
    return out


def test_regen_stamps_stale_dossier_state_when_hash_drifts(tmp_path):
    """A dossier whose `last_reviewed_against_hash` no longer matches the
    primitive's current `structural_hash` should be stamped
    `dossier_state: "stale"` by the v2 regen pipeline."""
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def widget():\n    return 1\n")

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    widget_node = next(
        n for n in _live_nodes(depgraph) if n["id"].endswith("::widget")
    )
    initial_hash = widget_node["structural_hash"]
    dossier_path = depgraph / widget_node["dossier"]
    assert dossier_path.exists()

    # Simulate a reviewer signing off — flip status to current, keep the
    # pinned hash where it is (so the dossier "matches" the corpus today).
    text = dossier_path.read_text()
    text = text.replace("status: unreviewed", "status: current")
    dossier_path.write_text(text)

    # Drift the source so structural_hash changes; the pinned hash in the
    # dossier is now out of date.
    (api / "core.py").write_text(
        "def widget(extra_param):\n    return extra_param + 1\n"
    )
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "detect stale dossiers" in r.stdout

    widget_after = next(
        n for n in _live_nodes(depgraph) if n["id"].endswith("::widget")
    )
    assert widget_after["structural_hash"] != initial_hash, (
        "structural_hash should have changed after the signature edit"
    )
    assert widget_after.get("dossier_state") == "stale", (
        f"expected dossier_state=stale on drifted node; got "
        f"{widget_after.get('dossier_state')!r}"
    )


def test_regen_does_not_stamp_stale_on_fresh_stubs(tmp_path):
    """Freshly-stubbed dossiers pin the just-computed `structural_hash`, so
    the stale pass running immediately after must not flag them. (Stamping
    every node `stale` on first regen would defeat the state machine.)"""
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def widget():\n    return 1\n")

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    for node in _live_nodes(depgraph):
        # On a fresh corpus, no node should be stamped stale — the pinned
        # hash in every stub matches the corresponding structural_hash.
        assert node.get("dossier_state") != "stale", (
            f"fresh stub flagged stale: {node['id']}"
        )


def test_regen_meta_records_stale_dossier_count(tmp_path):
    """`_meta.json` exposes `stale_dossier_count` so `health` and similar
    one-shot reporters don't have to re-walk the dossier corpus."""
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def widget():\n    return 1\n")

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    meta_path = depgraph / "nodes" / "_meta.json"
    meta = json.loads(meta_path.read_text())
    # First regen: nothing stale (all stubs are fresh).
    assert meta.get("stale_dossier_count") == 0

    # Drift the source so the existing dossier's pin no longer matches.
    (api / "core.py").write_text(
        "def widget(extra_param):\n    return extra_param + 1\n"
    )
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    meta = json.loads(meta_path.read_text())
    assert meta.get("stale_dossier_count", 0) >= 1, (
        f"expected stale_dossier_count >= 1 after drift; got {meta!r}"
    )
