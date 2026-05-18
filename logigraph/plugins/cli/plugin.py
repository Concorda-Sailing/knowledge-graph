"""CLI-tool plugin.

Activates on conventional CLI shapes: a `bin/*` executable, a Python
package with `__main__.py`, or a top-level `cli.py`. The detector is
intentionally permissive — false positives just mean a few extra cue
strings active, which is harmless.

Contributes:
  - entrypoint_kinds={"command"} for the hypothetical depgraph `kind=command`
    classification (not emitted today; future extractor work). Until that
    lands, CLI flows surface via path-glob fallbacks in process-rank
    rather than the kind-based entrypoint check.
  - sink_kinds={"util"} reflecting that CLI tools converge on shared
    utility modules rather than ORM models.
  - No `mutation_methods` (CLIs use argv, not HTTP verbs) — empty set
    means "no method filter applies."
  - test_path_globs covering pytest + unittest conventions.
  - headless_skip_kinds excludes only `test`, so background-job-style
    CLI subcommands can surface in headless-flow analysis.
"""
from kg.shared.plugins import Plugin

from logigraph.plugins.base import LogigraphCues


def _detect(repo_path):
    return (
        bool(list(repo_path.glob("bin/*")))
        or bool(list(repo_path.glob("**/__main__.py")))
        or bool(list(repo_path.glob("cli.py")))
        or bool(list(repo_path.glob("**/cli.py")))
    )


PLUGIN = Plugin(
    name="cli",
    detect=_detect,
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"command"},
        sink_kinds={"util"},
        test_path_globs={
            "**/tests/**", "**/test_*.py", "**/*_test.py",
        },
        headless_skip_kinds={"test"},
        kind_weights={
            "util": 1.0,
            "service": 0.65,
        },
    )},
)
