"""Built-in tool handler behaviors — read-only views over a fake corpus."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depgraph.lib.summarizer.tools import ToolContext, builtin_tool_handlers


def _ctx(tmp_path: Path) -> tuple[ToolContext, Path]:
    """Build a tiny fake repo + nodes_by_id + dependents index under tmp_path."""
    repo = tmp_path / "myrepo"
    repo.mkdir()
    (repo / "a.py").write_text("def foo():\n    return 1\n\nbar = 2\n")
    (repo / "b.py").write_text("\n".join(f"line {i}" for i in range(1, 30)) + "\n")

    nodes_by_id = {
        "api::a.py::foo": {
            "id": "api::a.py::foo",
            "primitive": "function",
            "kind": "service",
            "name": "foo",
            "owner": None,
            "source": {"repo": "api", "path": "a.py", "language": "python",
                       "line": 1, "end_line": 2},
            "signature": {"parameters": [], "return_type": None},
            "attributes": {},
            "edges_out": [
                {"target": "api::a.py::bar", "kind": "reads"},
                {"target": "api::a.py::bar", "kind": "reads"},
                {"target": "external::pypi::os", "kind": "imports"},
            ],
        },
    }
    deps_idx = {
        "api::a.py::foo": [
            {"source": "api::b.py::caller", "kind": "calls",
             "via": "function_call", "where": "b.py:42",
             "confidence": "exact"},
        ],
    }
    ctx = ToolContext(
        data_dir=tmp_path / "data",
        repos={"api": repo},
        dependents_index=deps_idx,
        nodes_by_id=nodes_by_id,
    )
    return ctx, repo


def test_read_source_returns_numbered_lines(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    handlers = builtin_tool_handlers(ctx)
    out = handlers["read_source"]({
        "repo": "api", "path": "a.py", "start_line": 1, "end_line": 4,
    })
    assert "    1  def foo():" in out
    assert "    3  " in out  # blank line at line 3


def test_read_source_rejects_unknown_repo(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["read_source"]({
        "repo": "ghost", "path": "x", "start_line": 1, "end_line": 1,
    })
    assert "not in [repos.*]" in out


def test_read_source_refuses_path_escape(tmp_path: Path) -> None:
    """Path traversal out of the repo root must be rejected."""
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["read_source"]({
        "repo": "api", "path": "../../etc/passwd",
        "start_line": 1, "end_line": 1,
    })
    assert "escapes repo root" in out


def test_read_source_truncates_past_400_lines(tmp_path: Path) -> None:
    ctx, repo = _ctx(tmp_path)
    big = repo / "big.py"
    big.write_text("\n".join(f"l{i}" for i in range(1, 1000)) + "\n")
    out = builtin_tool_handlers(ctx)["read_source"]({
        "repo": "api", "path": "big.py", "start_line": 1, "end_line": 999,
    })
    assert "truncated to 400 lines" in out


def test_read_source_file_not_found(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["read_source"]({
        "repo": "api", "path": "missing.py", "start_line": 1, "end_line": 5,
    })
    assert "file not found" in out


def test_dependents_of_lists_callers(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["dependents_of"]({"node_id": "api::a.py::foo"})
    assert "1 dependent(s)" in out
    assert "api::b.py::caller" in out
    assert "calls" in out


def test_dependents_of_for_unknown_node(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["dependents_of"]({"node_id": "ghost"})
    assert "no dependents recorded" in out


def test_node_info_returns_structured_summary(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["node_info"]({"node_id": "api::a.py::foo"})
    parsed = json.loads(out)
    assert parsed["primitive"] == "function"
    assert parsed["source"]["repo"] == "api"
    assert parsed["edges_out_summary"] == {"reads": 2, "imports": 1}


def test_node_info_returns_edges_by_kind_excluding_defines(tmp_path: Path) -> None:
    """`edges_out_by_kind` must enumerate outgoing edges grouped by kind
    so the dossier-draft prompt has detail to render `## Dependencies`.
    `defines` edges are intrinsic to the node and excluded from this
    detailed view (still counted in `edges_out_summary`)."""
    ctx, _ = _ctx(tmp_path)
    # Augment the foo node with a `defines` edge to verify it's filtered.
    ctx.nodes_by_id["api::a.py::foo"]["edges_out"].append(
        {"target": "api::a.py::foo.inner", "kind": "defines"}
    )
    out = builtin_tool_handlers(ctx)["node_info"]({"node_id": "api::a.py::foo"})
    parsed = json.loads(out)

    by_kind = parsed["edges_out_by_kind"]
    assert "defines" not in by_kind, "defines edges must be excluded from edges_out_by_kind"
    assert sorted(by_kind) == ["imports", "reads"]
    assert len(by_kind["reads"]) == 2
    assert by_kind["reads"][0]["target"] == "api::a.py::bar"
    assert by_kind["imports"][0]["target"] == "external::pypi::os"
    # Summary still counts defines (it's the count-by-kind, not the
    # dependency view).
    assert parsed["edges_out_summary"]["defines"] == 1


def test_node_info_caps_per_kind_edges(tmp_path: Path) -> None:
    """High-fan-out nodes must not blow the context window. Per-kind
    list is capped at 30."""
    ctx, _ = _ctx(tmp_path)
    big_edges = [
        {"target": f"api::other.py::sym{i}", "kind": "calls"}
        for i in range(50)
    ]
    ctx.nodes_by_id["api::a.py::foo"]["edges_out"] = big_edges
    out = builtin_tool_handlers(ctx)["node_info"]({"node_id": "api::a.py::foo"})
    parsed = json.loads(out)
    assert len(parsed["edges_out_by_kind"]["calls"]) == 30
    assert parsed["edges_out_summary"]["calls"] == 50


def test_node_info_unknown(tmp_path: Path) -> None:
    ctx, _ = _ctx(tmp_path)
    out = builtin_tool_handlers(ctx)["node_info"]({"node_id": "ghost"})
    assert "no node" in out


def test_recent_history_returns_git_log_or_message(tmp_path: Path) -> None:
    """Plant a real .git so the tool can run `git log`. The fixture's commits
    are minimal — we just assert no crash and that something printable returns."""
    import subprocess as sp
    ctx, repo = _ctx(tmp_path)
    sp.run(["git", "init", "-q", str(repo)], check=True)
    sp.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    sp.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    sp.run(["git", "-C", str(repo), "add", "."], check=True)
    sp.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    out = builtin_tool_handlers(ctx)["recent_history"]({
        "repo": "api", "path": "a.py", "limit": 5,
    })
    assert "init" in out
