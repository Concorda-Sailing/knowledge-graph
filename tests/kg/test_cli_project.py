"""Tests for kg project subcommand group."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

TOOL_ROOT = Path(__file__).resolve().parents[2]
KG_BIN = TOOL_ROOT / "bin" / "kg"


@pytest.fixture
def two_projects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    """Register two projects with full data-dir layouts."""
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    monkeypatch.delenv("KG_PROJECT", raising=False)
    monkeypatch.delenv("DEPGRAPH_DATA_DIR", raising=False)
    monkeypatch.delenv("LOGIGRAPH_DATA_DIR", raising=False)

    def make(name: str) -> Path:
        root = tmp_path / f"{name}-knowledge-graph"
        (root / "depgraph" / "nodes").mkdir(parents=True)
        (root / "logigraph" / "nodes").mkdir(parents=True)
        (root / "project.toml").write_text(
            f'[project]\nname = "{name}"\nsubsystems = ["depgraph", "logigraph"]\n'
        )
        (root / "depgraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        (root / "logigraph" / "project.toml").write_text(
            f'[project]\nname = "{name}"\n'
        )
        return root

    a = make("alpha")
    b = make("beta")
    subprocess.run([sys.executable, str(KG_BIN), "project", "add", str(a)], check=True,
                   env={**os.environ, "KG_REGISTRY_PATH": str(reg)})
    subprocess.run([sys.executable, str(KG_BIN), "project", "add", str(b)], check=True,
                   env={**os.environ, "KG_REGISTRY_PATH": str(reg)})
    return {"alpha": a, "beta": b, "registry": reg, "tmp_path": tmp_path}


def _run(env_reg: Path, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "KG_REGISTRY_PATH": str(env_reg)}
    return subprocess.run(
        [sys.executable, str(KG_BIN), *args],
        capture_output=True, text=True, env=env, cwd=cwd,
    )


def test_list_shows_two_projects(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "list")
    assert res.returncode == 0
    assert "alpha" in res.stdout
    assert "beta" in res.stdout


def test_use_then_list_marks_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "list")
    assert "* alpha" in res.stdout
    assert "  beta" in res.stdout  # 2-space prefix = not default


def test_use_clear_unsets_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "use", "--clear")
    assert res.returncode == 0
    res = _run(two_projects["registry"], "project", "list")
    assert "* alpha" not in res.stdout


def test_use_unknown_project_errors(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "use", "ghost")
    assert res.returncode != 0
    assert "not registered" in res.stderr


def test_current_reports_source(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "beta")
    res = _run(two_projects["registry"], "project", "current")
    assert "beta" in res.stdout
    assert "kg-graphs.toml default" in res.stdout


def test_show_prints_resolved_project(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "show")
    assert res.returncode == 0
    assert "alpha" in res.stdout
    assert str(two_projects["alpha"]) in res.stdout


def test_show_named_project_overrides_default(two_projects: dict) -> None:
    _run(two_projects["registry"], "project", "use", "alpha")
    res = _run(two_projects["registry"], "project", "show", "beta")
    assert "beta" in res.stdout
    assert str(two_projects["beta"]) in res.stdout


def test_remove_unregisters(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "remove", "alpha")
    assert res.returncode == 0
    list_res = _run(two_projects["registry"], "project", "list")
    assert "alpha" not in list_res.stdout


def test_init_scaffolds_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reg = tmp_path / "kg-graphs.toml"
    monkeypatch.setenv("KG_REGISTRY_PATH", str(reg))
    project_root = tmp_path / "fresh"
    res = _run(reg, "project", "init", str(project_root))
    assert res.returncode == 0
    assert (project_root / "knowledge-graph" / "depgraph" / "project.toml").exists()
    assert (project_root / "knowledge-graph" / "logigraph" / "project.toml").exists()


def test_add_repo_via_kg_project_writes_subtable(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    cfg_text = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert "[repos.api]" in cfg_text
    assert "path = " in cfg_text


def test_list_repos_via_kg_project(two_projects: dict) -> None:
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(two_projects["registry"], "project", "--project", "alpha", "list-repos")
    assert res.returncode == 0
    assert "api" in res.stdout


def test_remove_repo_via_kg_project(two_projects: dict) -> None:
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(two_projects["registry"], "project", "--project", "alpha", "remove-repo", "api")
    assert res.returncode == 0
    cfg_text = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert "[repos.api]" not in cfg_text


def test_add_repo_mirrors_into_logigraph(two_projects: dict) -> None:
    """add-repo writes [repos.<key>] into BOTH depgraph and logigraph
    project.toml so the logigraph hook can classify the repo's edits (#20)."""
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    logi_text = (two_projects["alpha"] / "logigraph" / "project.toml").read_text()
    assert "[repos.api]" in logi_text
    assert "path = " in logi_text


def test_remove_repo_strips_from_logigraph(two_projects: dict) -> None:
    """remove-repo removes the mirrored [repos.<key>] from logigraph too (#20)."""
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake-repo"),
    )
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "remove-repo", "api",
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    logi_text = (two_projects["alpha"] / "logigraph" / "project.toml").read_text()
    assert "[repos.api]" not in logi_text


def test_set_primary_repo(two_projects: dict) -> None:
    # Add a repo first so primary_repo has a valid target.
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake"),
    )
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "api",
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    cfg = (two_projects["alpha"] / "depgraph" / "project.toml").read_text()
    assert 'primary_repo = "api"' in cfg


def test_set_primary_repo_inserts_inside_project_section(
    two_projects: dict,
) -> None:
    """The key must land inside [project] as a sibling of `name`, NOT
    immediately above the next table header. A reader seeing
    `primary_repo = "api"` directly above `[repos.api]` would reasonably
    conclude it belongs to that repo's table (#31)."""
    _run(
        two_projects["registry"], "project", "--project", "alpha",
        "add-repo", "api", str(two_projects["tmp_path"] / "fake"),
    )
    cfg_path = two_projects["alpha"] / "depgraph" / "project.toml"
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "api",
    )
    assert res.returncode == 0, f"stderr: {res.stderr}"
    text = cfg_path.read_text()

    name_idx = text.index('name =')
    primary_idx = text.index('primary_repo =')
    repos_idx = text.index('[repos.api]')

    # primary_repo lives AFTER `name` but BEFORE `[repos.api]`.
    assert name_idx < primary_idx < repos_idx, (
        f"primary_repo at {primary_idx}; name at {name_idx}; [repos.api] at "
        f"{repos_idx}. Full toml:\n{text}"
    )
    # And it lives "close" to `name` — not just before the table header.
    # Strict check: no commented `[repos.*]` example between `name` and
    # `primary_repo`. The previous bug planted `primary_repo` after such
    # comments, immediately above the real table.
    intermediate = text[primary_idx:repos_idx]
    assert "# [repos." not in text[name_idx:primary_idx], (
        f"primary_repo landed below a commented example block; visually it "
        f"reads as part of the example, not as a [project] sibling. "
        f"Between name and primary_repo: {text[name_idx:primary_idx]!r}"
    )


def test_write_toml_key_inserts_after_last_assignment_not_before_table(
    tmp_path,
) -> None:
    """Focused unit test for the placement helper — reproduces the exact
    file shape from #31 (commented `[repos.web]` example sitting in the
    [project] body) and asserts the new key lands next to `name`, not
    just above the [repos.api] header."""
    from kg.cli.project import _write_toml_key

    cfg = tmp_path / "project.toml"
    cfg.write_text(
        '[project]\n'
        'name = "myproject"\n'
        '\n'
        '# Example — replace with your repos:\n'
        '#\n'
        '# [repos.web]\n'
        '# path = "~/<project>-web"\n'
        '# languages = ["typescript"]\n'
        '\n'
        '[repos.api]\n'
        'path = "~/myproject-api"\n'
    )
    _write_toml_key(cfg, "project", "primary_repo", "api")
    text = cfg.read_text()

    name_idx = text.index('name =')
    primary_idx = text.index('primary_repo =')
    table_idx = text.index('[repos.api]')

    assert name_idx < primary_idx < table_idx
    # The new key must NOT sit below the commented example.
    between_name_and_primary = text[name_idx:primary_idx]
    assert "# [repos." not in between_name_and_primary, (
        f"primary_repo landed below the commented example. Full file:\n{text}"
    )
    # The commented block and the real table both still appear, in order.
    assert text.index('# [repos.web]') > primary_idx
    assert text.index('[repos.api]') > text.index('# [repos.web]')


def test_write_toml_key_idempotent_replaces_existing(tmp_path) -> None:
    """Re-setting the same key updates in place rather than duplicating."""
    from kg.cli.project import _write_toml_key

    cfg = tmp_path / "project.toml"
    cfg.write_text('[project]\nname = "x"\nprimary_repo = "old"\n')
    _write_toml_key(cfg, "project", "primary_repo", "new")
    text = cfg.read_text()
    assert text.count("primary_repo") == 1
    assert 'primary_repo = "new"' in text
    assert 'primary_repo = "old"' not in text


def test_write_toml_key_into_empty_section_inserts_at_top(tmp_path) -> None:
    """A section that exists but has no key=value entries yet gets the
    new key right after its header."""
    from kg.cli.project import _write_toml_key

    cfg = tmp_path / "project.toml"
    cfg.write_text('[project]\n\n[repos.api]\npath = "x"\n')
    _write_toml_key(cfg, "project", "primary_repo", "api")
    text = cfg.read_text()
    # After [project], the very next non-blank line is the new key.
    project_idx = text.index("[project]")
    after = text[project_idx + len("[project]\n"):]
    first_nonblank = next(l for l in after.splitlines() if l.strip())
    assert first_nonblank == 'primary_repo = "api"', f"got: {first_nonblank!r}\n\n{text}"


def test_set_rejects_non_whitelist_field(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "wild_field", "value",
    )
    assert res.returncode != 0
    assert "not in whitelist" in res.stderr.lower()


def test_set_primary_repo_rejects_unknown_key(two_projects: dict) -> None:
    res = _run(
        two_projects["registry"], "project", "--project", "alpha",
        "set", "primary_repo", "missing-key",
    )
    assert res.returncode != 0


def test_health_runs_subsystem_checks(two_projects: dict) -> None:
    res = _run(two_projects["registry"], "project", "--project", "alpha", "health")
    # Exit code is allowed to be 0 or 1 depending on whether subsystems are
    # populated — but the output must mention both subsystems.
    out = res.stdout + res.stderr
    assert "depgraph" in out.lower()
    assert "logigraph" in out.lower()
