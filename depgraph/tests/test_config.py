"""Tests for lib.config additions — {kg_dir} substitution and repo_detectors."""
from pathlib import Path

import depgraph.lib.config as config
from depgraph.lib.config import repo_detectors


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
