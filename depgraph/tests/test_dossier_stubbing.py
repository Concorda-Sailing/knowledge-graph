"""#40: v2 regen stubs missing dossiers so `missing` is no longer the
dominant steady-state and downstream commands can rely on `unreviewed`
as the entry point for human review."""
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
    out = []
    for f in nodes.rglob("*.json"):
        if f.name.startswith("_") or any(p.startswith("_") for p in f.relative_to(nodes).parts):
            continue
        try:
            out.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            pass
    return out


def test_regen_writes_stubs_for_stubbable_kinds(tmp_path):
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text(
        "class Widget:\n"
        "    pass\n\n"
        "def helper():\n"
        "    return 1\n"
    )
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"
    assert "stub missing dossiers" in r.stdout

    depgraph = umbrella / "depgraph"
    nodes = _live_nodes(depgraph)
    by_id = {n["id"]: n for n in nodes}

    widget_id = next(i for i in by_id if i.endswith("::Widget"))
    helper_id = next(i for i in by_id if i.endswith("::helper"))

    # Stubbable kinds carry a `dossier` field after regen.
    widget = by_id[widget_id]
    helper = by_id[helper_id]
    assert widget.get("dossier"), f"class node missing dossier path: {widget}"
    assert helper.get("dossier"), f"function node missing dossier path: {helper}"

    # And the stub files exist on disk with the expected frontmatter.
    for node in (widget, helper):
        stub = depgraph / node["dossier"]
        assert stub.exists(), f"stub missing for {node['id']}: {stub}"
        text = stub.read_text()
        assert "status: unreviewed" in text
        assert f"last_reviewed_against_hash: {node['structural_hash']}" in text
        assert node["id"] in text


def test_regen_skips_stubs_for_modules_packages_variables(tmp_path):
    umbrella, api = _project_layout(tmp_path)
    (api / "constants.py").write_text("MAX = 1\n")
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    depgraph = umbrella / "depgraph"
    for node in _live_nodes(depgraph):
        if node.get("primitive") in {"module", "package", "variable"}:
            assert not node.get("dossier"), (
                f"{node['primitive']} node should not be stubbed: {node['id']}"
            )


def test_regen_is_idempotent_for_existing_dossiers(tmp_path):
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def fn():\n    pass\n")
    assert _regen(umbrella, api).returncode == 0
    depgraph = umbrella / "depgraph"
    nodes = _live_nodes(depgraph)
    fn_node = next(n for n in nodes if n["id"].endswith("::fn"))
    stub_path = depgraph / fn_node["dossier"]

    # Hand-write content that simulates manual review.
    custom = stub_path.read_text().replace("status: unreviewed", "status: current")
    custom = custom.replace("_TODO: describe", "Real description.")
    stub_path.write_text(custom)

    # Re-regen should not overwrite the customized dossier.
    assert _regen(umbrella, api).returncode == 0
    assert stub_path.read_text() == custom


def test_dossier_archived_alongside_node_on_source_delete(tmp_path):
    umbrella, api = _project_layout(tmp_path)
    (api / "doomed.py").write_text("def doomed():\n    pass\n")
    assert _regen(umbrella, api).returncode == 0

    depgraph = umbrella / "depgraph"
    doomed_node = next(
        n for n in _live_nodes(depgraph) if n["id"].endswith("::doomed")
    )
    dossier_rel = doomed_node["dossier"]
    dossier_path = depgraph / dossier_rel
    assert dossier_path.exists()

    # Delete source, re-regen → both node and dossier should land in archive.
    (api / "doomed.py").unlink()
    assert _regen(umbrella, api).returncode == 0

    # Dossier file no longer at canonical path.
    assert not dossier_path.exists(), "dossier should have been moved out"
    # And exists in dossiers/_archive.
    archived = list((depgraph / "dossiers" / "_archive").glob("*.md"))
    assert archived, "expected dossier in dossiers/_archive after archival"


def test_only_unreviewed_no_longer_conflates_missing(tmp_path):
    """Regression for the post-#40 cleanup: a regen'd corpus surfaces every
    non-skipped node as `unreviewed`, so `--only-unreviewed` rests on the
    state machine rather than the `missing` fallback that #35 added."""
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def fn():\n    pass\n")
    assert _regen(umbrella, api).returncode == 0

    result = subprocess.run(
        [
            sys.executable, "-m", "kg.cli",
            "depgraph", "dossier-rank", "--only-unreviewed",
            "--data-dir", str(umbrella),
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    # Should have surfaced our fn node as unreviewed (not filtered out).
    assert "fn" in result.stdout, (
        f"--only-unreviewed should surface stubbed nodes; got:\n{result.stdout}"
    )
