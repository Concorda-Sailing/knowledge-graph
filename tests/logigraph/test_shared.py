"""Direct tests for logigraph.lib.cli._shared helpers.

Uses the `data_dir` fixture from tests/logigraph/conftest.py.
The autouse `_logigraph_lib_on_path` fixture in the same conftest
ensures the logigraph version of `lib` is active for every test here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from logigraph.lib.cli._shared import (
    find_rules_for_target,
    load_all_nodes,
    load_depgraph_corpus,
    repo_relative,
    resolve_node_path,
)
from logigraph.lib.cli.context import Context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_logigraph_node(
    ctx: Context,
    node_id: str,
    *,
    kind: str = "rule",
    subdir: str = "rules",
) -> Path:
    """Write a minimal logigraph node JSON under nodes/<subdir>/."""
    node_file = ctx.NODES / subdir / f"{node_id.replace('::', '__')}.json"
    node_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "schema_version": 1,
        "id": node_id,
        "kind": kind,
        "title": "Test node",
    }
    node_file.write_text(json.dumps(data))
    return node_file


def _write_by_code_index(ctx: Context, mapping: dict[str, list[str]]) -> None:
    """Write a synthetic by_code index (depgraph-node-id → [rule-ids])."""
    idx_path = ctx.NODES / "_index" / "by_code.json"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(json.dumps({"schema_version": 1, "by_target": mapping}))


def _write_by_file_index(ctx: Context, mapping: dict[str, list[str]]) -> None:
    """Write a synthetic by_file index (basename/rel → [rule-ids])."""
    idx_path = ctx.NODES / "_index" / "by_file.json"
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    idx_path.write_text(json.dumps({"schema_version": 1, "by_file": mapping}))


# ---------------------------------------------------------------------------
# find_rules_for_target — three branches
# ---------------------------------------------------------------------------

def test_find_rules_for_target_rule_prefix_returns_verbatim(data_dir: Path) -> None:
    """A target starting with 'rule::' is returned as-is (no index lookup)."""
    ctx = Context.from_data_dir(data_dir)
    rule_id = "rule::auth::require_email_verified"

    result = find_rules_for_target(ctx, rule_id)

    assert result == [rule_id]


def test_find_rules_for_target_domain_prefix_returns_verbatim(data_dir: Path) -> None:
    """A target starting with a domain subkind prefix is returned as-is."""
    ctx = Context.from_data_dir(data_dir)
    domain_id = "role::member::admin"

    result = find_rules_for_target(ctx, domain_id)

    assert result == [domain_id]


def test_find_rules_for_target_depgraph_node_id_looks_up_by_code(data_dir: Path) -> None:
    """A target containing '::' (but not a domain prefix) is looked up via by_code."""
    ctx = Context.from_data_dir(data_dir)
    depgraph_id = "concorda-api::models/user.py::User"
    rule_ids = ["rule::auth::email_verified", "rule::auth::require_login"]
    _write_by_code_index(ctx, {depgraph_id: rule_ids})

    result = find_rules_for_target(ctx, depgraph_id)

    assert result == rule_ids


def test_find_rules_for_target_depgraph_id_missing_from_index_returns_empty(
    data_dir: Path,
) -> None:
    """A depgraph node id not present in the by_code index returns []."""
    ctx = Context.from_data_dir(data_dir)
    _write_by_code_index(ctx, {})

    result = find_rules_for_target(ctx, "concorda-api::models/foo.py::Foo")

    assert result == []


def test_find_rules_for_target_path_looks_up_by_file(tmp_path: Path) -> None:
    """A file-path target is resolved through by_file via repo_relative."""
    # Set up a repo checkout so path_to_repo_relative can match.
    repo_dir = tmp_path / "myproject-api"
    repo_dir.mkdir()
    src_file = repo_dir / "models" / "user.py"
    src_file.parent.mkdir(parents=True)
    src_file.touch()

    data_dir = tmp_path / "logigraph"
    (data_dir / "nodes" / "_index").mkdir(parents=True)
    (data_dir / "dossiers").mkdir()
    (data_dir / "calibration").mkdir()
    (data_dir / "telemetry").mkdir()
    depgraph_dir = tmp_path / "fake-depgraph"
    (depgraph_dir / "nodes").mkdir(parents=True)
    (depgraph_dir / "project.toml").write_text('[project]\nname = "fake"\n')
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n'
        f'[depgraph]\ndata_dir = "{depgraph_dir}"\n\n'
        f'[repos.api]\npath = "{repo_dir}"\n'
    )

    ctx = Context.from_data_dir(data_dir)
    key = "myproject-api/models/user.py"
    rule_ids = ["rule::auth::user_model"]
    _write_by_file_index(ctx, {key: rule_ids})

    result = find_rules_for_target(ctx, str(src_file))

    assert result == rule_ids


# ---------------------------------------------------------------------------
# load_all_nodes
# ---------------------------------------------------------------------------

def test_load_all_nodes_returns_all_authored_nodes(data_dir: Path) -> None:
    """load_all_nodes returns all non-underscore node files across kinds."""
    ctx = Context.from_data_dir(data_dir)

    rule_id = "rule::auth::require_login"
    process_id = "process::auth::login_flow"
    domain_id = "role::member::admin"

    _make_logigraph_node(ctx, rule_id, kind="rule", subdir="rules")
    _make_logigraph_node(ctx, process_id, kind="process", subdir="processes")
    _make_logigraph_node(ctx, domain_id, kind="domain", subdir="domain")

    result = load_all_nodes(ctx)

    assert rule_id in result
    assert process_id in result
    assert domain_id in result
    assert len(result) == 3


def test_load_all_nodes_skips_underscore_files(data_dir: Path) -> None:
    """Files/dirs starting with _ are not loaded as nodes."""
    ctx = Context.from_data_dir(data_dir)
    # Write a real node.
    _make_logigraph_node(ctx, "rule::x::y", kind="rule", subdir="rules")
    # Write an index/meta file that must be skipped.
    (ctx.NODES / "_meta.json").write_text(json.dumps({"schema_version": 1}))
    (ctx.NODES / "_index" / "by_code.json").write_text(json.dumps({"by_target": {}}))

    result = load_all_nodes(ctx)

    assert "rule::x::y" in result
    assert len(result) == 1


def test_load_all_nodes_skips_invalid_json(
    data_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A file with invalid JSON produces a WARN and is skipped."""
    ctx = Context.from_data_dir(data_dir)
    bad_file = ctx.NODES / "rules" / "broken.json"
    bad_file.parent.mkdir(parents=True, exist_ok=True)
    bad_file.write_text("NOT VALID JSON")

    result = load_all_nodes(ctx)

    assert result == {}
    captured = capsys.readouterr()
    assert "WARN" in captured.err


def test_load_all_nodes_skips_nodes_without_id(data_dir: Path) -> None:
    """A node file that has no 'id' field is silently skipped."""
    ctx = Context.from_data_dir(data_dir)
    no_id_file = ctx.NODES / "rules" / "noid.json"
    no_id_file.parent.mkdir(parents=True, exist_ok=True)
    no_id_file.write_text(json.dumps({"schema_version": 1, "kind": "rule"}))

    result = load_all_nodes(ctx)

    assert result == {}


# ---------------------------------------------------------------------------
# load_depgraph_corpus
# ---------------------------------------------------------------------------

def test_load_depgraph_corpus_returns_depgraph_nodes(data_dir: Path) -> None:
    """load_depgraph_corpus reads nodes from ctx.depgraph_dir/nodes."""
    ctx = Context.from_data_dir(data_dir)
    dnode_dir = ctx.depgraph_dir / "nodes"
    dnode_dir.mkdir(parents=True, exist_ok=True)

    dnode_id = "concorda-api::models/user.py::User"
    dnode_file = dnode_dir / "user__User.json"
    dnode_file.write_text(json.dumps({
        "schema_version": 1,
        "id": dnode_id,
        "kind": "model",
        "source": {"repo": "concorda-api", "path": "models/user.py"},
    }))

    result = load_depgraph_corpus(ctx)

    assert dnode_id in result
    assert result[dnode_id]["kind"] == "model"


def test_load_depgraph_corpus_returns_empty_when_no_nodes_dir(
    data_dir: Path,
) -> None:
    """If the depgraph nodes directory does not exist, returns empty dict."""
    ctx = Context.from_data_dir(data_dir)
    # The depgraph_dir exists but has no 'nodes' subdir.
    import shutil
    shutil.rmtree(ctx.depgraph_dir / "nodes", ignore_errors=True)

    result = load_depgraph_corpus(ctx)

    assert result == {}


def test_load_depgraph_corpus_skips_underscore_files(data_dir: Path) -> None:
    """Underscore-prefixed files in the depgraph nodes dir are skipped."""
    ctx = Context.from_data_dir(data_dir)
    dnode_dir = ctx.depgraph_dir / "nodes"
    dnode_dir.mkdir(parents=True, exist_ok=True)

    # Real node
    real_id = "api::models/order.py::Order"
    (dnode_dir / "order.json").write_text(json.dumps({
        "schema_version": 1,
        "id": real_id,
        "kind": "model",
    }))
    # Meta file — must be skipped
    (dnode_dir / "_meta.json").write_text(json.dumps({"schema_version": 1}))

    result = load_depgraph_corpus(ctx)

    assert real_id in result
    assert len(result) == 1


# ---------------------------------------------------------------------------
# repo_relative
# ---------------------------------------------------------------------------

def test_repo_relative_returns_basename_and_rel_for_known_repo(tmp_path: Path) -> None:
    """repo_relative returns (basename, rel) for a path inside a configured repo."""
    repo_dir = tmp_path / "myproject-api"
    repo_dir.mkdir()
    src = repo_dir / "routes" / "auth.py"
    src.parent.mkdir(parents=True)
    src.touch()

    data_dir = tmp_path / "logigraph"
    (data_dir / "nodes" / "_index").mkdir(parents=True)
    (data_dir / "dossiers").mkdir()
    (data_dir / "calibration").mkdir()
    (data_dir / "telemetry").mkdir()
    depgraph_dir = tmp_path / "fake-depgraph"
    (depgraph_dir / "nodes").mkdir(parents=True)
    (depgraph_dir / "project.toml").write_text('[project]\nname = "fake"\n')
    (data_dir / "project.toml").write_text(
        f'[project]\nname = "test"\n\n'
        f'[depgraph]\ndata_dir = "{depgraph_dir}"\n\n'
        f'[repos.api]\npath = "{repo_dir}"\n'
    )

    ctx = Context.from_data_dir(data_dir)
    result = repo_relative(ctx, str(src))

    assert result is not None
    basename, rel = result
    assert basename == "myproject-api"
    assert rel == "routes/auth.py"


def test_repo_relative_returns_none_for_unmatched_path(data_dir: Path) -> None:
    """repo_relative returns None for a path not under any configured repo."""
    ctx = Context.from_data_dir(data_dir)
    # data_dir has no [repos.*] configured.
    result = repo_relative(ctx, "/some/completely/unrelated/path.py")
    assert result is None


# ---------------------------------------------------------------------------
# resolve_node_path
# ---------------------------------------------------------------------------

def test_resolve_node_path_rule_id_returns_correct_path(data_dir: Path) -> None:
    """resolve_node_path for a rule id returns the correct JSON path."""
    ctx = Context.from_data_dir(data_dir)
    rule_id = "rule::auth::require_email_verified"

    result = resolve_node_path(ctx, rule_id)

    expected = ctx.NODES / "rules" / "auth__require_email_verified.json"
    assert result == expected


def test_resolve_node_path_domain_id_returns_correct_path(data_dir: Path) -> None:
    """resolve_node_path for a domain/role id returns the correct JSON path."""
    ctx = Context.from_data_dir(data_dir)
    domain_id = "role::member::admin"

    result = resolve_node_path(ctx, domain_id)

    expected = ctx.NODES / "domain" / "role__member__admin.json"
    assert result == expected


def test_resolve_node_path_process_id_returns_correct_path(data_dir: Path) -> None:
    """resolve_node_path for a process id returns the correct JSON path."""
    ctx = Context.from_data_dir(data_dir)
    process_id = "process::auth::login_flow"

    result = resolve_node_path(ctx, process_id)

    expected = ctx.NODES / "processes" / "auth__login_flow.json"
    assert result == expected


def test_resolve_node_path_unknown_prefix_returns_none(data_dir: Path) -> None:
    """resolve_node_path returns None for an unrecognized id prefix."""
    ctx = Context.from_data_dir(data_dir)

    result = resolve_node_path(ctx, "unknown::something::here")

    assert result is None
