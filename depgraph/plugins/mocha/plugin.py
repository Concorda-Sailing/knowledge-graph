"""Mocha test-framework plugin.

Activates when `mocha` is in npm deps, or a Mocha config marker exists
(.mocharc.*). Contributes the canonical Mocha BDD-style primitives so
the test classifier excludes them from `tests` edges (they're framework
machinery, not code under test).

Doc references:
  https://mochajs.org/  (BDD interfaces: describe, it, before, after, …)
"""
from kg.shared.plugins import Plugin, has_marker_file, has_npm_dep

from depgraph.lib.classification.config import LanguageCues


def _detect(repo_path):
    return (
        has_npm_dep(repo_path, "mocha")
        or has_marker_file(
            repo_path,
            ".mocharc.js", ".mocharc.cjs", ".mocharc.json",
            ".mocharc.yml", ".mocharc.yaml",
        )
    )


PLUGIN = Plugin(
    name="mocha",
    detect=_detect,
    target_versions={"mocha": "10.7"},
    cues={
        "typescript": LanguageCues(
            test_framework_primitives={
                "describe", "context",                  # BDD suite
                "it", "specify",                        # BDD test
                "before", "after",                      # suite hooks
                "beforeEach", "afterEach",              # test hooks
            },
        ),
    },
)
