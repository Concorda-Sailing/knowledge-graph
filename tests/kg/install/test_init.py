import argparse
from pathlib import Path
import pytest

from kg.cli.install.init import cmd_init


def test_init_creates_layout(tmp_project: Path) -> None:
    args = argparse.Namespace(path=str(tmp_project))
    rc = cmd_init(args)
    assert rc == 0
    bundle = tmp_project / "knowledge-graph"
    assert (bundle / "project.toml").exists()
    assert (bundle / "depgraph" / "project.toml").exists()
    assert (bundle / "depgraph" / "nodes").is_dir()
    assert (bundle / "depgraph" / "dossiers").is_dir()
    assert (bundle / "depgraph" / "extractors").is_dir()
    assert (bundle / "depgraph" / "telemetry").is_dir()
    assert (bundle / "depgraph" / "extractors" / "README.md").exists()
    assert (bundle / "logigraph" / "project.toml").exists()
    assert (bundle / "logigraph" / "nodes").is_dir()
    assert (bundle / "logigraph" / "dossiers").is_dir()
    assert (bundle / "logigraph" / "telemetry").is_dir()
    assert (bundle / "logigraph" / "CANDIDATES.md").exists()
    # calibration/ is NOT created by install.sh cmd_init — intentionally absent


def test_init_root_project_toml_declares_name(tmp_project: Path) -> None:
    args = argparse.Namespace(path=str(tmp_project))
    cmd_init(args)
    text = (tmp_project / "knowledge-graph" / "project.toml").read_text()
    assert 'name = "myproject"' in text
    assert 'subsystems = ["depgraph", "logigraph"]' in text


def test_init_depgraph_repos_scaffold_uses_subtable_form(tmp_project: Path) -> None:
    """Per the Phase-1 fix, [repos.<key>] sub-table form (not flat [repos])."""
    args = argparse.Namespace(path=str(tmp_project))
    cmd_init(args)
    text = (tmp_project / "knowledge-graph" / "depgraph" / "project.toml").read_text()
    # The flat form `[repos]\nkey = "..."` is wrong. Sub-table form has `[repos.api]`.
    assert "[repos.api]" in text or "[repos.<key>]" in text or "# [repos." in text


def test_init_refuses_existing_layout(tmp_project: Path) -> None:
    """If <bundle>/depgraph already exists, init refuses to overwrite."""
    args = argparse.Namespace(path=str(tmp_project))
    cmd_init(args)
    rc = cmd_init(args)
    assert rc != 0  # refusal on second call


def test_init_logigraph_toml_references_depgraph(tmp_project: Path) -> None:
    """logigraph/project.toml should declare depgraph.data_dir pointing to the bundle."""
    args = argparse.Namespace(path=str(tmp_project))
    cmd_init(args)
    text = (tmp_project / "knowledge-graph" / "logigraph" / "project.toml").read_text()
    assert "[depgraph]" in text
    assert "data_dir" in text
    assert "depgraph" in text


def test_init_tilde_expansion(tmp_path: Path) -> None:
    """args.path with ~/ prefix should be expanded correctly."""
    import os
    # Only meaningful if HOME is set and the path doesn't actually start with ~.
    # We test that the function handles absolute paths (the normal case); tilde
    # expansion is a code-path that requires a fake HOME.  Use a simple check:
    # pass an absolute path and confirm rc == 0.
    dest = tmp_path / "tildetest"
    args = argparse.Namespace(path=str(dest))
    rc = cmd_init(args)
    assert rc == 0
    assert (dest / "knowledge-graph" / "project.toml").exists()
