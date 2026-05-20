"""#58: regen detects inbound-edge drift on dossier-bearing nodes and
stamps `inbound_drift` on every primitive whose consumer set has
shifted by ≥ 3 OR ≥ 25% since the dossier's
`last_reviewed_inbound_count` was last pinned.

Inverse failure mode from #57 (which catches drift in the node's OWN
source via `structural_hash`). The `## External consumers` /
`## Dependencies` sections of a dossier are baked prose grounded in
inbound/outgoing edges — when the edge set shifts but the node's body
doesn't, the prose rots silently. This test exercises the case the
issue describes verbatim: a hub node whose consumer count grows while
its own source is unchanged.
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


def _find(depgraph: Path, *, id_suffix: str) -> dict:
    return next(n for n in _live_nodes(depgraph) if n["id"].endswith(id_suffix))


def test_regen_stamps_inbound_drift_when_consumer_set_grows(tmp_path):
    """A hub node whose consumer set grows past the threshold between
    two regens must be stamped with `inbound_drift` — even though the
    hub's own source is unchanged and its `structural_hash` therefore
    hasn't moved. This is the scenario the issue body describes:
    External consumers prose rots silently because hash-based
    staleness can't see consumer-set growth.

    Each `from hub import hub; hub()` caller contributes two inbound
    edges to hub (`imports` + `calls`); `defines` edges from the
    parent module are excluded by the detector. So 1 caller → 2
    inbound edges, 5 callers → 10 edges, delta=8 — well past the
    absolute threshold of 3.
    """
    umbrella, api = _project_layout(tmp_path)
    # First pass: one consumer of `hub` (2 edges: imports + calls).
    (api / "hub.py").write_text("def hub():\n    return 1\n")
    (api / "caller_a.py").write_text("from hub import hub\n\ndef a():\n    return hub()\n")

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    hub_node = _find(depgraph, id_suffix="hub.py::hub")
    initial_hash = hub_node["structural_hash"]
    dossier_path = depgraph / hub_node["dossier"]
    assert dossier_path.exists()

    # The stub must pin the just-observed (non-`defines`) inbound count
    # so future drift detection has a baseline.
    text = dossier_path.read_text()
    assert "last_reviewed_inbound_count: 2" in text, (
        f"expected stub to pin 2 inbound edges (imports + calls from "
        f"caller_a); frontmatter was:\n{text.splitlines()[:10]!r}"
    )
    # Simulate a reviewer finalizing the dossier: flip status to current
    # and leave the auto-stubbed pinned count intact.
    dossier_path.write_text(text.replace("status: unreviewed", "status: current"))

    # Second pass: add 4 more callers of `hub`. Consumer-edge count
    # goes 2 → 10 (delta=+8, well past the absolute threshold of 3).
    # hub's own source is untouched, so its structural_hash stays put
    # — only inbound drift fires.
    for letter in ("b", "c", "d", "e"):
        (api / f"caller_{letter}.py").write_text(
            f"from hub import hub\n\ndef {letter}():\n    return hub()\n"
        )

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "detect inbound-edge drift" in r.stdout

    hub_after = _find(depgraph, id_suffix="hub.py::hub")
    assert hub_after["structural_hash"] == initial_hash, (
        "hub's own source is unchanged; structural_hash must not move "
        "(otherwise this test would be exercising #57's hash-drift "
        "path instead of #58's inbound-drift path)"
    )
    drift = hub_after.get("inbound_drift")
    assert drift is not None, (
        f"expected `inbound_drift` stamp on hub after consumer-edge set "
        f"grew 2→10; got {hub_after.get('inbound_drift')!r}"
    )
    assert drift["pinned_count"] == 2
    assert drift["current_count"] == 10
    assert drift["delta"] == 8
    # 8 / 2 = 4.0 exactly.
    assert drift["pct"] == 4.0


def test_regen_does_not_stamp_inbound_drift_when_unchanged(tmp_path):
    """A node whose consumer set hasn't moved must not be flagged. The
    no-op regen case has to stay quiet or the signal is useless on
    routine corpora."""
    umbrella, api = _project_layout(tmp_path)
    (api / "hub.py").write_text("def hub():\n    return 1\n")
    (api / "caller_a.py").write_text(
        "from hub import hub\n\ndef a():\n    return hub()\n"
    )

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    # Second regen with no source changes whatsoever. Every dossier
    # should remain unstamped; the inbound counts haven't moved an inch.
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    for node in _live_nodes(depgraph):
        assert "inbound_drift" not in node, (
            f"steady-state regen flagged inbound drift on {node['id']!r}: "
            f"{node.get('inbound_drift')!r}"
        )


def test_regen_does_not_stamp_drift_on_small_subthreshold_swing(tmp_path):
    """Drift smaller than the absolute floor (3) AND below the relative
    threshold (25%) must not fire. The thresholds exist specifically to
    keep noise out — if a tiny swing on a large-fanout hub fired the
    signal, the dashboard would be useless.

    Setup: start with 10 callers (20 inbound edges). Add one more
    caller (+2 edges → 22). delta=2, pct=0.10 — below both thresholds.
    """
    umbrella, api = _project_layout(tmp_path)
    (api / "hub.py").write_text("def hub():\n    return 1\n")
    for letter in "abcdefghij":
        (api / f"caller_{letter}.py").write_text(
            f"from hub import hub\n\ndef {letter}():\n    return hub()\n"
        )

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    hub_node = _find(depgraph, id_suffix="hub.py::hub")
    dossier_path = depgraph / hub_node["dossier"]
    assert "last_reviewed_inbound_count: 20" in dossier_path.read_text(), (
        f"expected 20-edge baseline (10 callers × 2 edges each); got "
        f"frontmatter:\n{dossier_path.read_text().splitlines()[:10]!r}"
    )

    # Add ONE more caller: 20 → 22 edges. delta=2, pct=0.10. Neither
    # threshold fires; the dossier must stay unflagged.
    (api / "caller_k.py").write_text(
        "from hub import hub\n\ndef k():\n    return hub()\n"
    )
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    hub_after = _find(depgraph, id_suffix="hub.py::hub")
    assert "inbound_drift" not in hub_after, (
        f"+1 caller on a 10-consumer hub (+10% bump) is below both "
        f"thresholds; got {hub_after.get('inbound_drift')!r}"
    )


def test_regen_meta_records_inbound_drift_count(tmp_path):
    """`_meta.json` exposes `inbound_drift_count` so health and similar
    one-shot reporters don't have to re-walk the corpus to compute it."""
    umbrella, api = _project_layout(tmp_path)
    (api / "hub.py").write_text("def hub():\n    return 1\n")
    (api / "caller_a.py").write_text(
        "from hub import hub\n\ndef a():\n    return hub()\n"
    )

    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    meta = json.loads((depgraph / "nodes" / "_meta.json").read_text())
    # First regen: every stub's pin matches the just-measured count.
    assert meta.get("inbound_drift_count") == 0

    # Drift the consumer set past the threshold and re-regen.
    for letter in ("b", "c", "d", "e"):
        (api / f"caller_{letter}.py").write_text(
            f"from hub import hub\n\ndef {letter}():\n    return hub()\n"
        )
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    meta = json.loads((depgraph / "nodes" / "_meta.json").read_text())
    assert meta.get("inbound_drift_count", 0) >= 1, (
        f"expected inbound_drift_count >= 1 after consumer-set growth; "
        f"got {meta!r}"
    )
