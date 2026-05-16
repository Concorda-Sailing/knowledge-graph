"""Tests for lib.config.render_extractor — specifically the {framework_dir}
substitution that lets project.toml reference framework-shipped extractors."""
from pathlib import Path
import depgraph.lib.config as config


def test_framework_dir_substitution():
    repo_info = {
        "path": "/some/repo",
        "extractor": ["python3", "{framework_dir}/extractors/generic/foo.py", "--path", "{path}"],
    }
    out = config.render_extractor(repo_info, Path("/some/data_dir"))
    assert out is not None
    # framework_dir resolves to the depgraph repo root (parent of lib/).
    expected_root = str(Path(config.__file__).resolve().parent.parent)
    assert out[1].startswith(expected_root)
    assert out[1].endswith("/extractors/generic/foo.py")
    assert out[3] == "/some/repo"


def test_existing_substitutions_unchanged():
    """Make sure the original {data_dir} and {path} substitutions still work."""
    repo_info = {"path": "/r", "extractor": ["x", "{data_dir}/y", "{path}/z"]}
    out = config.render_extractor(repo_info, Path("/d"))
    assert out == ["x", "/d/y", "/r/z"]
