"""Tests for lib.config additions — {kg_dir} substitution and repo_detectors."""
from pathlib import Path

import pytest

import depgraph.lib.config as config
from depgraph.lib.config import repo_detectors, resolve_data_dir


# ---------------------------------------------------------------------------
# resolve_data_dir registry fallback
# ---------------------------------------------------------------------------

def test_resolve_data_dir_falls_back_to_registry_default(tmp_path, monkeypatch):
    """With no env var and a cwd outside any project, resolve_data_dir resolves
    the kg registry's default project — so the bare `depgraph` binary works from
    any directory (regression for the first-run "DATA_DIR not set" fumble)."""
    proj = tmp_path / "proj-knowledge-graph"
    (proj / "depgraph" / "nodes").mkdir(parents=True)
    (proj / "depgraph" / "project.toml").write_text('[project]\nname = "proj"\n')

    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "kg-graphs.toml").write_text(
        f'default = "proj"\n\n[[graph]]\nname = "proj"\npath = "{proj}"\n'
    )

    monkeypatch.setenv("HOME", str(home))          # Path.home() honors $HOME on POSIX
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)                     # cwd is not inside a project

    assert resolve_data_dir("DEPGRAPH_DATA_DIR") == (proj / "depgraph").resolve()


def test_resolve_data_dir_env_var_beats_registry(tmp_path, monkeypatch):
    """An explicit env var still wins over the registry fallback."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "kg-graphs.toml").write_text(
        'default = "proj"\n\n[[graph]]\nname = "proj"\npath = "/some/other"\n'
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("DEPGRAPH_DATA_DIR", str(tmp_path / "explicit"))
    assert resolve_data_dir("DEPGRAPH_DATA_DIR") == (tmp_path / "explicit").resolve()


def test_resolve_data_dir_raises_when_no_default_registered(tmp_path, monkeypatch):
    """No env var, no project in cwd, no registry default → clear SystemExit."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "kg-graphs.toml").write_text("# empty\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        resolve_data_dir("DEPGRAPH_DATA_DIR")


# ---------------------------------------------------------------------------
# {kg_dir} substitution via render_extractor
# ---------------------------------------------------------------------------

def test_kg_dir_substitution(tmp_path):
    """render_extractor replaces {kg_dir} with the knowledge-graph framework root."""
    repo_info = {
        "path": str(tmp_path),
        "extractor": ["python3", "{kg_dir}/some/script.py"],
    }
    out = config.render_extractor(repo_info, tmp_path)
    assert out is not None
    expected_kg_dir = str(Path(config.__file__).resolve().parent.parent.parent)
    assert out[1] == f"{expected_kg_dir}/some/script.py"


def test_kg_dir_does_not_break_existing_substitutions(tmp_path):
    """Existing {data_dir}, {path}, {framework_dir} still work when {kg_dir} is also present."""
    repo_info = {
        "path": str(tmp_path),
        "extractor": [
            "{data_dir}/a",
            "{path}/b",
            "{framework_dir}/c",
            "{kg_dir}/d",
        ],
    }
    out = config.render_extractor(repo_info, tmp_path)
    assert out is not None
    expected_framework_dir = str(Path(config.__file__).resolve().parent.parent)
    expected_kg_dir = str(Path(config.__file__).resolve().parent.parent.parent)
    assert out[0] == f"{tmp_path}/a"
    assert out[1] == f"{tmp_path}/b"
    assert out[2] == f"{expected_framework_dir}/c"
    assert out[3] == f"{expected_kg_dir}/d"


# ---------------------------------------------------------------------------
# repo_detectors
# ---------------------------------------------------------------------------

def test_repo_detectors_returns_list():
    repo_cfg = {"path": "x", "extractor": ["python3", "y"], "detectors": ["fastapi", "pytest"]}
    assert repo_detectors(repo_cfg) == ["fastapi", "pytest"]


def test_repo_detectors_default_empty():
    repo_cfg = {"path": "x", "extractor": ["python3", "y"]}
    assert repo_detectors(repo_cfg) == []


def test_repo_detectors_raises_on_non_list():
    repo_cfg = {"path": "x", "detectors": "fastapi"}
    try:
        repo_detectors(repo_cfg)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "str" in str(exc)
