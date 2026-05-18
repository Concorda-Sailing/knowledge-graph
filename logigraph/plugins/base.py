"""Logigraph-specific cue type for the plugin registry.

The generic plugin machinery lives in `kg.shared.plugins` (Plugin
protocol, discovery, detection helpers). This module owns the
logigraph-side cue dataclass and the merger/copier callbacks the
generic registry delegates to when unioning cues across active plugins.

A `LogigraphCues` describes what counts as a flow entrypoint, a
state-mutating sink, a UI entry-path convention, and so on — the
per-framework knowledge that lets process-rank work on a CLI corpus
or a data-pipeline corpus without falling back to web-API defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LogigraphCues:
    """Per-framework cues for flow detection.

    Every field is a set so plugins compose by union — multiple active
    plugins contribute additively. Empty fields mean "no opinion"; the
    consuming code in `process.py` should treat an empty set as
    permissive (e.g. empty mutation_methods means every flow-initiator
    qualifies, not zero).
    """

    entrypoint_kinds: set[str] = field(default_factory=set)
    """Depgraph kinds whose nodes initiate a flow.

    Examples per framework category:
      web-api      -> {"endpoint"}
      cli          -> {"command"}
      event-driven -> {"handler"}
      pipeline     -> {"task", "stage"}
    """

    sink_kinds: set[str] = field(default_factory=set)
    """Depgraph kinds whose nodes represent state-mutation convergence.

    Examples:
      web-api      -> {"model"}
      cli          -> {"util"}      (CLI tools converge on shared utils)
      event-driven -> {"publisher"}
      pipeline     -> {"output"}
    """

    mutation_methods: set[str] = field(default_factory=set)
    """HTTP / RPC methods that imply state mutation.

    Empty set means no method filter — every flow-initiator counts (e.g.
    CLI commands, event handlers). When non-empty, endpoint ids whose
    leading method is not in this set are excluded from mutation-flow
    analysis. Convention: uppercase verbs.

    Example:
      web-api -> {"POST", "PUT", "DELETE", "PATCH"}
    """

    ui_entry_path_globs: set[str] = field(default_factory=set)
    """Gitignore-style globs marking files that are user-facing entry points.

    Examples:
      Next.js -> {"app/**/page.tsx", "pages/**/*.tsx"}
      Nuxt    -> {"pages/**/*.vue"}
    """

    api_client_path_globs: set[str] = field(default_factory=set)
    """Gitignore-style globs marking files that wrap API/RPC clients.

    Used by process-rank to elevate UI-flow candidates that traverse
    through a client wrapper before hitting an endpoint.
    """

    test_path_globs: set[str] = field(default_factory=set)
    """Globs marking a file as a test, so it can be excluded from
    flow heuristics (a function only called from tests doesn't count as
    a flow participant)."""

    headless_skip_kinds: set[str] = field(default_factory=set)
    """Depgraph kinds excluded from headless-flow detection.

    "Headless" flows are pipelines that don't start at a UI or HTTP
    entrypoint — background jobs, cron triggers, queue consumers. The
    detector iterates over candidates whose kind is NOT in this set.

    Examples:
      web-api      -> {"endpoint", "component", "test", "hook", "schema", "model"}
      cli          -> {"test"}    (CLI tools may legitimately have headless flows)
    """

    kind_weights: dict[str, float] = field(default_factory=dict)
    """Per-kind weights used by convergence-detection signals. Higher
    weights bias process-rank toward flows that converge on these kinds.

    Phase-1 lift of the hardcoded KIND_WEIGHT dict in process.py;
    Phase 2 (deferred) will refactor process-rank signals to be fully
    pluggable, at which point this field may shift shape.

    Example:
      web-api -> {"model": 1.0, "hook": 0.85, "service": 0.65, "schema": 0.45}
    """
