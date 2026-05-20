"""Pass A — structural classifier tests (#57).

The classifier is rule-based, so its behavior is fully observable from
plain Python inputs. No model mocking required.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from depgraph.lib.summarizer.classifier import (
    ClassifierResult,
    GitLogSignal,
    SalientEdge,
    format_classifier_block,
    run_classifier,
)


def _node(nid: str, *, kind: str = "service", edges_out: list[dict] | None = None) -> dict:
    return {
        "id": nid,
        "primitive": "function",
        "kind": kind,
        "name": nid.split("::")[-1],
        "source": {"repo": "api", "path": "a.py", "line": 1, "end_line": 5},
        "edges_out": edges_out or [],
    }


# ---------------------------------------------------------------------------
# node_kind — pass-through from the node dict
# ---------------------------------------------------------------------------


def test_node_kind_passes_through_from_node() -> None:
    node = _node("api::a.py::Foo", kind="model")
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.node_kind == "model"


def test_node_kind_falls_back_to_primitive_when_kind_missing() -> None:
    node = {
        "id": "api::a.py::raw",
        "primitive": "class",
        "source": {"repo": "api", "path": "a.py"},
    }
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.node_kind == "class"


def test_node_kind_unknown_when_both_missing() -> None:
    node = {"id": "x", "source": {"repo": "api", "path": "a.py"}}
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.node_kind == "unknown"


# ---------------------------------------------------------------------------
# salient_inbound_edges — rank by call-site density
# ---------------------------------------------------------------------------


def test_salient_inbound_ranks_by_call_site_density() -> None:
    """When one caller has 3 call sites and another has 1, the 3-site
    caller comes first regardless of alphabetical order."""
    deps = [
        {"source": "api::b.py::single", "kind": "calls", "via": "function_call"},
        {"source": "api::z.py::triple", "kind": "calls", "via": "function_call"},
        {"source": "api::z.py::triple", "kind": "calls", "via": "function_call"},
        {"source": "api::z.py::triple", "kind": "calls", "via": "function_call"},
    ]
    node = _node("api::a.py::foo")
    result = run_classifier(
        node,
        dependents_index={"api::a.py::foo": deps},
        nodes_by_id={},
    )
    assert len(result.salient_inbound_edges) == 2
    assert result.salient_inbound_edges[0].target == "api::z.py::triple"
    assert result.salient_inbound_edges[1].target == "api::b.py::single"


def test_salient_inbound_capped_at_limit() -> None:
    """More than the cap (_SALIENT_INBOUND_LIMIT=8) compresses to the cap."""
    deps = [
        {"source": f"api::f{i}.py::caller", "kind": "calls", "via": "fc"}
        for i in range(20)
    ]
    node = _node("api::a.py::hub")
    result = run_classifier(
        node,
        dependents_index={"api::a.py::hub": deps},
        nodes_by_id={},
    )
    assert len(result.salient_inbound_edges) == 8


def test_salient_inbound_empty_when_no_dependents() -> None:
    node = _node("api::a.py::lonely")
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.salient_inbound_edges == []


def test_salient_inbound_carries_where_and_confidence() -> None:
    deps = [{
        "source": "api::b.py::caller",
        "kind": "calls",
        "via": "function_call",
        "where": "b.py:42",
        "confidence": "exact",
    }]
    node = _node("api::a.py::foo")
    result = run_classifier(
        node,
        dependents_index={"api::a.py::foo": deps},
        nodes_by_id={},
    )
    edge = result.salient_inbound_edges[0]
    assert edge.where == "b.py:42"
    assert edge.confidence == "exact"
    assert edge.via == "function_call"


# ---------------------------------------------------------------------------
# salient_outbound_edges — grouped by kind
# ---------------------------------------------------------------------------


def test_salient_outbound_groups_by_kind() -> None:
    """Outbound edges should surface at least one per distinct kind so
    the prose pass sees the diversity of relationships, not just the
    densest one."""
    node = _node("api::a.py::svc", edges_out=[
        {"target": "external::pypi::os", "kind": "imports"},
        {"target": "api::a.py::Helper", "kind": "calls"},
        {"target": "api::a.py::Helper", "kind": "calls"},
        {"target": "api::base.py::Base", "kind": "extends"},
    ])
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    kinds = {e.kind for e in result.salient_outbound_edges}
    assert kinds == {"calls", "extends", "imports"}


def test_salient_outbound_caps_per_kind() -> None:
    """A burst of one kind shouldn't drown out the others — each kind
    capped at _SALIENT_OUTBOUND_PER_KIND_LIMIT=5."""
    edges = [
        {"target": f"api::z.py::Helper{i}", "kind": "calls"} for i in range(20)
    ] + [{"target": "api::base.py::Base", "kind": "extends"}]
    node = _node("api::a.py::svc", edges_out=edges)
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    calls = [e for e in result.salient_outbound_edges if e.kind == "calls"]
    extends = [e for e in result.salient_outbound_edges if e.kind == "extends"]
    assert len(calls) == 5
    assert len(extends) == 1


def test_salient_outbound_empty_for_leaf() -> None:
    node = _node("api::a.py::leaf", edges_out=[])
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.salient_outbound_edges == []


# ---------------------------------------------------------------------------
# test_coverage_hint
# ---------------------------------------------------------------------------


def test_coverage_hint_tested_when_dependent_is_test() -> None:
    deps = [{"source": "api::test_a.py::test_foo", "kind": "calls", "via": "fc"}]
    nodes = {
        "api::test_a.py::test_foo": {
            "id": "api::test_a.py::test_foo",
            "kind": "test",
            "primitive": "function",
        },
    }
    node = _node("api::a.py::foo")
    result = run_classifier(
        node,
        dependents_index={"api::a.py::foo": deps},
        nodes_by_id=nodes,
    )
    assert result.test_coverage_hint == "tested"


def test_coverage_hint_unknown_when_dependents_are_all_non_test() -> None:
    """Absence of test deps in our corpus is 'unknown', never
    'untested' — could be missing extraction (see classifier docstring)."""
    deps = [{"source": "api::b.py::caller", "kind": "calls", "via": "fc"}]
    nodes = {
        "api::b.py::caller": {
            "id": "api::b.py::caller",
            "kind": "service",
            "primitive": "function",
        },
    }
    node = _node("api::a.py::foo")
    result = run_classifier(
        node,
        dependents_index={"api::a.py::foo": deps},
        nodes_by_id=nodes,
    )
    assert result.test_coverage_hint == "unknown"


def test_coverage_hint_unknown_for_orphan() -> None:
    node = _node("api::a.py::lonely")
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.test_coverage_hint == "unknown"


# ---------------------------------------------------------------------------
# git_log_signal
# ---------------------------------------------------------------------------


def _init_repo_with_subjects(repo: Path, subjects: list[str]) -> None:
    """Build a tiny git repo with one commit per subject, all touching
    the same file. Used to exercise the git-log signal parser."""
    repo.mkdir(exist_ok=True)
    target = repo / "a.py"
    target.write_text("pass\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "init"], check=True)
    for i, subj in enumerate(subjects):
        target.write_text(f"pass  # {i}\n")
        subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", subj], check=True)


def test_git_signal_detects_fix_keyword(tmp_path: Path) -> None:
    _init_repo_with_subjects(tmp_path, ["fix: handle empty input"])
    node = _node("api::a.py::foo")
    result = run_classifier(
        node, dependents_index={}, nodes_by_id={}, repo_root=tmp_path
    )
    assert result.git_log_signal.recent_fix is True
    assert result.git_log_signal.recent_revert is False


def test_git_signal_detects_revert(tmp_path: Path) -> None:
    _init_repo_with_subjects(tmp_path, ["Revert \"add bad behavior\""])
    node = _node("api::a.py::foo")
    result = run_classifier(
        node, dependents_index={}, nodes_by_id={}, repo_root=tmp_path
    )
    assert result.git_log_signal.recent_revert is True


def test_git_signal_high_churn(tmp_path: Path) -> None:
    _init_repo_with_subjects(tmp_path, [f"chore: bump v{i}" for i in range(15)])
    node = _node("api::a.py::foo")
    result = run_classifier(
        node, dependents_index={}, nodes_by_id={}, repo_root=tmp_path
    )
    assert result.git_log_signal.high_churn is True
    assert result.git_log_signal.commits_in_window >= 10


def test_git_signal_ignores_non_keywords(tmp_path: Path) -> None:
    """A subject like 'prefix the constant' must not match 'fix' as a
    keyword (the parser should anchor to word boundaries)."""
    _init_repo_with_subjects(tmp_path, ["prefix the constant", "infix notation note"])
    node = _node("api::a.py::foo")
    result = run_classifier(
        node, dependents_index={}, nodes_by_id={}, repo_root=tmp_path
    )
    assert result.git_log_signal.recent_fix is False


def test_git_signal_no_repo_returns_empty_signal(tmp_path: Path) -> None:
    """Pointing at a directory without .git must not crash — empty signal."""
    node = _node("api::a.py::foo")
    result = run_classifier(
        node, dependents_index={}, nodes_by_id={}, repo_root=tmp_path
    )
    assert result.git_log_signal == GitLogSignal()


def test_git_signal_skipped_when_repo_root_is_none() -> None:
    node = _node("api::a.py::foo")
    result = run_classifier(node, dependents_index={}, nodes_by_id={})
    assert result.git_log_signal == GitLogSignal()


# ---------------------------------------------------------------------------
# format_classifier_block — Pass B prompt slot
# ---------------------------------------------------------------------------


def test_format_classifier_block_includes_all_fields() -> None:
    result = ClassifierResult(
        node_kind="model",
        coverage_caveats=["fk_references_not_extracted"],
        salient_inbound_edges=[
            SalientEdge(target="api::b.py::caller", kind="calls",
                        via="fc", where="b.py:42", confidence="exact"),
        ],
        salient_outbound_edges=[
            SalientEdge(target="api::base.py::Base", kind="extends"),
        ],
        git_log_signal=GitLogSignal(recent_fix=True, commits_in_window=3),
        test_coverage_hint="tested",
    )
    block = format_classifier_block(result)
    assert "node_kind: `model`" in block
    assert "test_coverage_hint: `tested`" in block
    assert "recent_fix=True" in block
    assert "commits_in_window=3" in block
    assert "fk_references_not_extracted" in block
    assert "api::b.py::caller" in block
    assert "api::base.py::Base" in block
    # Pass A is described as authoritative so Pass B reads it that way.
    assert "ground truth" in block.lower() or "authoritative" in block.lower()


def test_format_classifier_block_empty_edges_collapse_to_none() -> None:
    result = ClassifierResult(node_kind="util")
    block = format_classifier_block(result)
    # Both edge sections present with explicit "(none)" so Pass B can
    # tell empty-by-classifier from missing-from-prompt.
    assert "salient_inbound_edges" in block
    assert "salient_outbound_edges" in block
    assert "(none)" in block


def test_to_json_dict_serializes_cleanly() -> None:
    """`to_json_dict` should round-trip through `json.dumps` without
    custom encoders (everything is plain dataclasses or primitives)."""
    import json
    result = ClassifierResult(
        node_kind="service",
        salient_inbound_edges=[SalientEdge(target="x", kind="calls")],
    )
    s = json.dumps(result.to_json_dict())
    decoded = json.loads(s)
    assert decoded["node_kind"] == "service"
    assert decoded["salient_inbound_edges"][0]["target"] == "x"
