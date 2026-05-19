"""#42: v2 regen archives symbol-level orphans (function/class removed from
a file that still exists) using per-(repo, language) extraction manifests.
Manifest absence is the safety hatch for partial regens."""
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


def _live_ids(depgraph: Path) -> set[str]:
    nodes = depgraph / "nodes"
    ids: set[str] = set()
    for f in nodes.rglob("*.json"):
        if f.name.startswith("_") or any(p.startswith("_") for p in f.relative_to(nodes).parts):
            continue
        try:
            ids.add(json.loads(f.read_text())["id"])
        except (json.JSONDecodeError, KeyError):
            pass
    return ids


def test_regen_writes_manifest_per_repo_per_language(tmp_path):
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text("def fn():\n    pass\n")
    r = _regen(umbrella, api)
    assert r.returncode == 0, f"{r.stdout}\n{r.stderr}"

    manifest_dir = umbrella / "depgraph" / "nodes" / "_manifests"
    assert manifest_dir.exists()
    files = list(manifest_dir.glob("*.json"))
    assert files, "expected at least one manifest"
    manifest = json.loads(files[0].read_text())
    assert manifest["repo"] == "api"
    assert manifest["language"] == "python"
    assert any("fn" in nid for nid in manifest["node_ids"])


def test_regen_archives_function_removed_from_still_existing_file(tmp_path):
    umbrella, api = _project_layout(tmp_path)
    (api / "core.py").write_text(
        "def keep_me():\n    pass\n\n"
        "def remove_me():\n    pass\n"
    )
    assert _regen(umbrella, api).returncode == 0

    depgraph = umbrella / "depgraph"
    ids_before = _live_ids(depgraph)
    assert any("remove_me" in i for i in ids_before)

    # Remove the function, keep the file.
    (api / "core.py").write_text("def keep_me():\n    pass\n")
    r2 = _regen(umbrella, api)
    assert r2.returncode == 0, f"{r2.stdout}\n{r2.stderr}"
    assert "archive domain-orphans" in r2.stdout

    ids_after = _live_ids(depgraph)
    assert any("keep_me" in i for i in ids_after)
    assert not any("remove_me" in i for i in ids_after), (
        f"remove_me should have been archived as domain orphan; ids: {ids_after}"
    )

    # And there's an archived copy with the right reason stamp.
    archived = list((depgraph / "nodes" / "_archive").glob("*.json"))
    assert any(
        "remove_me" in (json.loads(f.read_text()).get("id") or "")
        and json.loads(f.read_text()).get("_archive_reason") == "domain_orphan_symbol_removed"
        for f in archived
    ), f"missing domain_orphan archive entry; saw {[json.loads(f.read_text()) for f in archived]}"


def test_partial_regen_does_not_touch_other_repos_nodes(tmp_path):
    """If a regen only touches one (repo, language), nodes from a different
    repo/language must stay put. The manifest gate is what enforces this."""
    umbrella = tmp_path / "project"
    umbrella.mkdir()
    depgraph = umbrella / "depgraph"
    nodes = depgraph / "nodes" / "modules"
    nodes.mkdir(parents=True)

    # Hand-place a node from a different repo that THIS regen never touches.
    other_node = nodes / "other__alive_py.json"
    other_node.write_text(json.dumps({
        "id": "other::alive.py::existing",
        "primitive": "function",
        "name": "existing",
        "source": {"repo": "other", "path": "alive.py", "language": "python"},
        "structural_hash": "deadbeef",
    }))

    # Regen `api` repo only.
    api = tmp_path / "api"
    api.mkdir()
    (api / "core.py").write_text("def fn():\n    pass\n")
    assert _regen(umbrella, api).returncode == 0

    # other-repo node should still be on disk — no manifest for (other, python).
    assert other_node.exists(), (
        "partial regen accidentally archived a node from an untouched repo"
    )


def test_manifest_not_written_on_ts_extractor_failure(tmp_path, monkeypatch):
    """If TS extraction fails mid-run, do NOT write a TS manifest — a partial
    extraction would otherwise look complete and the domain-orphan pass would
    archive everything the failed run didn't emit."""
    from depgraph.lib.cli import regen as regen_mod

    umbrella = tmp_path / "project"
    umbrella.mkdir()
    data_dir = umbrella / "depgraph"
    data_dir.mkdir()
    api = tmp_path / "api"
    api.mkdir()
    (api / "core.ts").write_text("export const x = 1;\n")

    # Force TS extractor to look like it failed. The third tuple element is
    # the resolver-stats dict added in #77 — empty on failure since the
    # sentinel ndjson line isn't emitted when the extractor exits non-zero.
    def _fake_ts_extract(*args, **kwargs):
        return [], {}, "exit=137; OOM"
    monkeypatch.setattr(regen_mod, "_extract_typescript", _fake_ts_extract)

    rc = regen_mod._run_v2_pipeline(
        data_dir=data_dir,
        repos=[{
            "key": "api",
            "path": api,
            "languages": ["typescript"],
            "migrations_dirs": [],
            "include_paths": None,
            "exclude_paths": None,
        }],
        tool_root=Path(__file__).resolve().parents[1],
    )
    # Pipeline returns non-zero because of the extractor error.
    assert rc != 0

    manifest_dir = data_dir / "nodes" / "_manifests"
    if manifest_dir.exists():
        ts_manifest = manifest_dir / "api__typescript.json"
        assert not ts_manifest.exists(), (
            "TS manifest must not be written on extractor failure"
        )
