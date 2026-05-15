"""Tests for bin/depgraph flag and unflag subcommands."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent
BIN = REPO / "bin" / "depgraph"


def _make_fixture(tmp_path: Path) -> Path:
    """Minimal depgraph data dir with one model node, initialized as a git repo."""
    nodes = tmp_path / "nodes" / "models"
    nodes.mkdir(parents=True)
    model = {
        "id": "test-api::models/foo.py::Foo",
        "kind": "model",
        "signature": {"kind": "model", "name": "Foo", "tablename": "foo"},
        "source": {"repo": "test-api", "path": "models/foo.py", "line": 1},
        "title": "Foo",
        "structural_hash": "deadbeef",
        "schema_version": 1,
        "depends_on": [],
        "dossier": "dossiers/models/test_api__models_foo_py__Foo.md",
        "external_consumers": [],
        "extractor": "test",
        "feature": None,
        "tests": [],
        "warnings": [],
    }
    (nodes / "test_api__models_foo_py__Foo.json").write_text(
        json.dumps(model, indent=2) + "\n"
    )
    (tmp_path / "nodes" / "_index").mkdir()
    (tmp_path / "project.toml").write_text(
        '[project]\nname = "test"\nprimary_repo = "api"\n[repos.api]\nbasename = "test-api"\npath = "/nonexistent"\n'
    )
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)
    return tmp_path


def _run(args, data):
    env = {
        "DEPGRAPH_DATA_DIR": str(data),
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": str(data),
    }
    return subprocess.run([str(BIN), *args], cwd=data, env=env, capture_output=True, text=True)


def test_depgraph_flag_sets_fields_and_commits(tmp_path):
    data = _make_fixture(tmp_path)
    r = _run(["flag", "test-api::models/foo.py::Foo", "--reason", "stale", "--actor", "alice"], data)
    assert r.returncode == 0, r.stderr
    node = json.loads((data / "nodes/models/test_api__models_foo_py__Foo.json").read_text())
    assert node["flagged"] is True
    assert node["flagged_by"] == "alice"
    assert node["flagged_at"]
    assert node["flagged_reason"] == "stale"
    log = subprocess.run(
        ["git", "log", "-1", "--format=%s%n%b"], cwd=data, capture_output=True, text=True
    )
    assert log.stdout.startswith("flag: test-api::models/foo.py::Foo")
    assert "stale" in log.stdout


def test_depgraph_unflag_clears_fields_and_commits(tmp_path):
    data = _make_fixture(tmp_path)
    _run(["flag", "test-api::models/foo.py::Foo", "--reason", "x"], data)
    r = _run(["unflag", "test-api::models/foo.py::Foo"], data)
    assert r.returncode == 0, r.stderr
    node = json.loads((data / "nodes/models/test_api__models_foo_py__Foo.json").read_text())
    assert "flagged" not in node or node["flagged"] is False
    assert "flagged_by" not in node
    assert "flagged_at" not in node
    assert "flagged_reason" not in node


def test_depgraph_flag_unknown_id_exits_1(tmp_path):
    data = _make_fixture(tmp_path)
    r = _run(["flag", "test-api::no::Such", "--reason", "x"], data)
    assert r.returncode == 1
    assert "no" in r.stderr.lower()


def test_depgraph_flag_no_reason_omits_flagged_reason(tmp_path):
    """flag with no --reason sets flagged=true but does not set flagged_reason."""
    data = _make_fixture(tmp_path)
    r = _run(["flag", "test-api::models/foo.py::Foo", "--actor", "alice"], data)
    assert r.returncode == 0, r.stderr
    node = json.loads((data / "nodes/models/test_api__models_foo_py__Foo.json").read_text())
    assert node["flagged"] is True
    assert node["flagged_by"] == "alice"
    assert "flagged_reason" not in node


def test_depgraph_unflag_not_flagged_exits_0_with_message(tmp_path):
    """unflag on a node that is not flagged exits 0 with a 'no change' message."""
    data = _make_fixture(tmp_path)
    r = _run(["unflag", "test-api::models/foo.py::Foo"], data)
    assert r.returncode == 0, r.stderr
    assert "no change" in r.stdout
