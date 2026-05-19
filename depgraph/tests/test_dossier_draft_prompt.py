"""Dossier-draft prompt construction tests — pin the structure of the
prompt and dossier template so #56 (outgoing-deps section) doesn't
regress.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from depgraph.lib.cli.dossier import (
    _GROUNDING_AND_SECTIONS,
    _build_full_prompt,
    _build_thin_prompt,
    _render_caveats_block,
)


def _ctx(data_dir: Path) -> SimpleNamespace:
    return SimpleNamespace(DEPGRAPH=data_dir)


def _node() -> dict:
    return {
        "id": "api::svc.py::process",
        "kind": "service",
        "primitive": "function",
        "structural_hash": "abcdef1234567890",
        "source": {"repo": "api", "path": "svc.py", "line": 10, "end_line": 30},
        "edges_out": [
            {"target": "api::base.py::BaseSvc", "kind": "extends",
             "via": "class_extends", "confidence": "exact", "where": "svc.py:11"},
            {"target": "external::pypi::sqlalchemy", "kind": "imports",
             "via": "from_import", "confidence": "exact", "where": "svc.py:3"},
            {"target": "api::util.py::helper", "kind": "calls",
             "via": "function_call", "confidence": "exact", "where": "svc.py:18"},
            {"target": "api::svc.py::process.local", "kind": "defines",
             "via": "scope_body", "confidence": "exact", "where": "svc.py:15"},
        ],
    }


def test_full_prompt_includes_outgoing_dependencies_block(tmp_path: Path):
    """The full-prompt path must surface the node's edges_out (minus
    `defines`) grouped by kind. Without this, the LLM is asked to write
    a `## Dependencies` section with no graph-supplied data — exactly
    the fabrication risk #56 was filed for."""
    node = _node()
    # Build the outgoing-edges string the way cmd_dossier_draft does.
    out_edges = [e for e in node["edges_out"] if e.get("kind") != "defines"]
    by_kind: dict[str, list[dict]] = {}
    for e in out_edges:
        by_kind.setdefault(e["kind"], []).append(e)
    buckets: list[str] = []
    for kind in sorted(by_kind):
        rows = by_kind[kind]
        buckets.append(f"  {kind} ({len(rows)}):")
        for e in rows:
            buckets.append(
                f"    - {e['target']}  (via {e['via']}, {e['confidence']}, {e['where']})"
            )
    out_str = "\n".join(buckets)

    prompt = _build_full_prompt(
        nid=node["id"], node=node, repo="api", rel="svc.py", line=10,
        src_excerpt="def process(): pass", deps_str="  (none)", deps_more="",
        n_deps=0, out_str=out_str, out_more="", n_out=len(out_edges),
        git_log="(empty)", adj_str="  (none)", rules_str="  (none)",
        caveats_str=_render_caveats_block([]),
        dossier_path=tmp_path / "dossiers" / "functions" / "p.md",
        ctx=_ctx(tmp_path),
    )

    assert "# Outgoing dependencies" in prompt
    assert "3 total" in prompt  # defines edge filtered out
    assert "calls (1):" in prompt
    assert "extends (1):" in prompt
    assert "imports (1):" in prompt
    assert "api::base.py::BaseSvc" in prompt
    assert "api::util.py::helper" in prompt
    assert "external::pypi::sqlalchemy" in prompt
    # `defines` edges are intrinsic to the node, not dependencies.
    assert "api::svc.py::process.local" not in prompt


def test_thin_prompt_includes_outgoing_count_and_node_info_instruction(tmp_path: Path):
    """Tools-mode path: surface the count + an explicit MUST-call
    instruction pointing at `node_info` so the model fetches the
    detailed edges_out_by_kind before drafting `## Dependencies`."""
    node = _node()
    n_out = len([e for e in node["edges_out"] if e["kind"] != "defines"])
    prompt = _build_thin_prompt(
        nid=node["id"], node=node, repo="api", rel="svc.py", line=10,
        read_start=5, read_end=35, n_deps=0, n_out=n_out,
        caveats_str=_render_caveats_block([]),
        dossier_path=tmp_path / "dossiers" / "functions" / "p.md",
        ctx=_ctx(tmp_path),
    )
    assert f"outgoing dependencies (edges_out excluding `defines`): {n_out}" in prompt
    assert f'node_info(node_id="{node["id"]}")' in prompt
    assert "## Dependencies" in prompt  # via _GROUNDING_AND_SECTIONS


def test_grounding_template_carries_dependencies_section():
    """The shared template must require a `## Dependencies` section
    between Invariants and Gotchas. Pin the order so re-orderings get
    caught."""
    text = _GROUNDING_AND_SECTIONS
    assert "## Dependencies" in text
    inv = text.index("## Invariants")
    deps = text.index("## Dependencies")
    cross = text.index("## Cross-cutting concerns")
    assert inv < deps < cross, (
        "Dependencies must slot between Invariants and Cross-cutting concerns"
    )


def test_render_caveats_block_lists_enum_and_description():
    """When the node has caveats stamped, the rendered block must carry
    both the enum (so the dossier can mirror it verbatim) and the
    registry's long description (so the model has the language to
    write the prose). See #55."""
    rendered = _render_caveats_block([
        "orm_relationships_not_extracted",
        "fk_references_not_extracted",
    ])
    assert "`orm_relationships_not_extracted`" in rendered
    assert "`fk_references_not_extracted`" in rendered
    # Long description text from the registry — verifies we resolved
    # through caveat_description, not just rendered the enum twice.
    assert "ORM" in rendered or "relationship(" in rendered


def test_render_caveats_block_empty_falls_through_cleanly():
    rendered = _render_caveats_block([])
    assert "(none stamped)" in rendered


def test_grounding_template_carries_coverage_caveats_section():
    """The `## Coverage caveats` section must slot before `## External
    consumers` and after `## Cross-cutting concerns` so the reader sees
    the gap-acknowledgment before the (necessarily-incomplete) consumer
    list."""
    text = _GROUNDING_AND_SECTIONS
    assert "## Coverage caveats" in text
    cross = text.index("## Cross-cutting concerns")
    caveats = text.index("## Coverage caveats")
    consumers = text.index("## External consumers")
    assert cross < caveats < consumers


def test_full_prompt_surfaces_stamped_caveats(tmp_path: Path):
    """End-to-end through `_build_full_prompt`: a node with caveats
    stamped on it has the rendered block reach the prompt body."""
    node = _node()
    node["coverage_caveats"] = ["orm_relationships_not_extracted"]
    prompt = _build_full_prompt(
        nid=node["id"], node=node, repo="api", rel="svc.py", line=10,
        src_excerpt="class Foo: pass", deps_str="  (none)", deps_more="",
        n_deps=0, out_str="  (none)", out_more="", n_out=0,
        git_log="(empty)", adj_str="  (none)", rules_str="  (none)",
        caveats_str=_render_caveats_block(node["coverage_caveats"]),
        dossier_path=tmp_path / "dossiers" / "classes" / "f.md",
        ctx=_ctx(tmp_path),
    )
    assert "# Coverage caveats" in prompt
    assert "`orm_relationships_not_extracted`" in prompt
