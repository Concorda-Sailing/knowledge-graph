"""Pass A → Pass B integration tests for dossier-draft (#57).

These tests verify the seam between the structural classifier (Pass A)
and the prose-drafting prompt builders (Pass B). They're located in
`tests/lib/summarizer/` rather than `tests/cli/` because the contract
under test is "Pass A output flows into the Pass B prompt verbatim" —
which is a summarizer-package invariant, not a CLI argparse concern.

The prompt builders are imported with their underscore-prefixed names
intentionally: they're the concrete seam between the two passes and the
underscore is a "callers in this package only" convention, not a hide.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from depgraph.lib.cli.dossier import _build_full_prompt, _build_thin_prompt
from depgraph.lib.summarizer.classifier import (
    ClassifierResult,
    GitLogSignal,
    SalientEdge,
    format_classifier_block,
)


class _StubCtx:
    """Minimal Context stand-in: only `DEPGRAPH` is read by the builders
    (for the `dossier_path.relative_to(ctx.DEPGRAPH)` formatting)."""

    def __init__(self, depgraph: Path):
        self.DEPGRAPH = depgraph


def _sample_result() -> ClassifierResult:
    return ClassifierResult(
        node_kind="model",
        coverage_caveats=["orm_relationships_not_extracted"],
        salient_inbound_edges=[
            SalientEdge(target="api::b.py::caller", kind="calls",
                        via="function_call", where="b.py:42",
                        confidence="exact"),
        ],
        salient_outbound_edges=[
            SalientEdge(target="api::base.py::Base", kind="extends",
                        via=""),
        ],
        git_log_signal=GitLogSignal(recent_fix=True, commits_in_window=4),
        test_coverage_hint="tested",
    )


# Defaults for the prompt-builder kwargs added since #56 / #55 landed
# (28baf60 outgoing-deps section; cb0d2eb coverage caveats). Tests don't
# exercise those code paths; pass empty/no-op values.
_OUT_KW = dict(out_str="  (none)", out_more="", n_out=0)
_CAVEATS_KW = dict(caveats_str="")


# ---------------------------------------------------------------------------
# Pass A output appears verbatim in both prompt builders
# ---------------------------------------------------------------------------


def test_full_prompt_embeds_classifier_block(tmp_path: Path) -> None:
    """The full (pre-loaded) prompt must include the formatted Pass A
    output. The prose head reads it as ground truth instead of being
    asked to re-derive structure."""
    ctx = _StubCtx(tmp_path)
    dossier_path = tmp_path / "dossiers" / "models" / "x.md"
    block = format_classifier_block(_sample_result())
    prompt = _build_full_prompt(
        nid="api::a.py::X",
        node={"kind": "model", "structural_hash": "abc123def4567"},
        repo="api", rel="a.py", line=1,
        src_excerpt="    1  pass",
        deps_str="  (none)", deps_more="",
        n_deps=0, git_log="(no recent commits)",
        adj_str="  (none)", rules_str="  (none)",
        dossier_path=dossier_path, ctx=ctx,
        classifier_block=block,
        **_OUT_KW, **_CAVEATS_KW,
    )
    # The whole block, with its header, must be present verbatim.
    assert block in prompt
    # And the specific fact strings should show up — sanity that the
    # interpolation didn't drop sections.
    assert "node_kind: `model`" in prompt
    assert "api::b.py::caller" in prompt
    assert "recent_fix=True" in prompt


def test_thin_prompt_embeds_classifier_block(tmp_path: Path) -> None:
    """Tools-mode (thin) prompt must also embed Pass A output. The
    tool-driven exploration still happens, but the head no longer has
    to classify in the same turn as it writes prose."""
    ctx = _StubCtx(tmp_path)
    dossier_path = tmp_path / "dossiers" / "models" / "x.md"
    block = format_classifier_block(_sample_result())
    prompt = _build_thin_prompt(
        nid="api::a.py::X",
        node={"kind": "model", "structural_hash": "abc123def4567"},
        repo="api", rel="a.py", line=1,
        read_start=1, read_end=70, n_deps=0,
        dossier_path=dossier_path, ctx=ctx,
        classifier_block=block,
        n_out=0, **_CAVEATS_KW,
    )
    assert block in prompt
    assert "node_kind: `model`" in prompt
    assert "api::b.py::caller" in prompt


def test_classifier_block_appears_before_grounding_rules(tmp_path: Path) -> None:
    """Pass A facts must appear earlier in the prompt than the GROUNDING
    RULES section — the rules reference 'the Pass A structural facts
    above' so the order matters for the prose head's reading."""
    ctx = _StubCtx(tmp_path)
    block = format_classifier_block(_sample_result())
    prompt = _build_full_prompt(
        nid="api::a.py::X",
        node={"kind": "model", "structural_hash": "abc123def4567"},
        repo="api", rel="a.py", line=1,
        src_excerpt="    1  pass",
        deps_str="  (none)", deps_more="",
        n_deps=0, git_log="(no commits)",
        adj_str="  (none)", rules_str="  (none)",
        dossier_path=tmp_path / "x.md", ctx=ctx,
        classifier_block=block,
        **_OUT_KW, **_CAVEATS_KW,
    )
    pos_block = prompt.find("Pass A output")
    pos_rules = prompt.find("GROUNDING RULES")
    assert pos_block != -1 and pos_rules != -1
    assert pos_block < pos_rules


# ---------------------------------------------------------------------------
# Pass B prompts are well-formed without a classifier block (defensive)
# ---------------------------------------------------------------------------


def test_full_prompt_without_classifier_block_still_renders(tmp_path: Path) -> None:
    """The classifier_block default is "" so callers who haven't migrated
    yet (or who deliberately skip Pass A) get a usable prompt."""
    ctx = _StubCtx(tmp_path)
    prompt = _build_full_prompt(
        nid="api::a.py::X",
        node={"kind": "model", "structural_hash": "abc"},
        repo="api", rel="a.py", line=1,
        src_excerpt="    1  pass",
        deps_str="  (none)", deps_more="",
        n_deps=0, git_log="(none)",
        adj_str="  (none)", rules_str="  (none)",
        dossier_path=tmp_path / "x.md", ctx=ctx,
        **_OUT_KW, **_CAVEATS_KW,
    )
    assert "GROUNDING RULES" in prompt
    assert "## Purpose" in prompt
    # Without a classifier block the "Pass A output" header should be absent.
    assert "Pass A output" not in prompt


def test_thin_prompt_without_classifier_block_still_renders(tmp_path: Path) -> None:
    ctx = _StubCtx(tmp_path)
    prompt = _build_thin_prompt(
        nid="api::a.py::X",
        node={"kind": "model", "structural_hash": "abc"},
        repo="api", rel="a.py", line=1,
        read_start=1, read_end=70, n_deps=0,
        dossier_path=tmp_path / "x.md", ctx=ctx,
        n_out=0, **_CAVEATS_KW,
    )
    assert "Required exploration" in prompt
    assert "Pass A output" not in prompt


# ---------------------------------------------------------------------------
# Pass B prompt re-states that Pass A facts are authoritative
# ---------------------------------------------------------------------------


def test_grounding_rules_reference_pass_a(tmp_path: Path) -> None:
    """The grounding rules must tell the prose head to treat the Pass A
    facts as authoritative. Without that, the head is free to disagree
    with the structured classifier — defeating the point of the split."""
    ctx = _StubCtx(tmp_path)
    block = format_classifier_block(_sample_result())
    prompt = _build_full_prompt(
        nid="api::a.py::X",
        node={"kind": "model", "structural_hash": "abc"},
        repo="api", rel="a.py", line=1,
        src_excerpt="    1  pass",
        deps_str="(none)", deps_more="",
        n_deps=0, git_log="(none)",
        adj_str="(none)", rules_str="(none)",
        dossier_path=tmp_path / "x.md", ctx=ctx,
        classifier_block=block,
        **_OUT_KW, **_CAVEATS_KW,
    )
    # The exact phrasing in dossier.py is "The Pass A structural facts
    # above are authoritative." Search for the discriminating bit.
    assert "Pass A structural facts above are authoritative" in prompt
