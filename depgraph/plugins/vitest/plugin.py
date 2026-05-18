"""Vitest test-framework plugin.

Activates when `vitest` is a project dependency or a `vitest.config.*` marker
exists. Vitest's globals match Jest's almost exactly, so a project that has
either is well-served by these cues; the `jest` plugin (separate) covers the
Jest-only case for projects without Vitest installed.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_marker_file, has_npm_dep

PLUGIN = Plugin(
    name="vitest",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "vitest")
        or has_marker_file(repo_path, "vitest.config.ts", "vitest.config.js",
                           "vitest.config.mts", "vitest.config.cts")
    ),
    target_versions={"vitest": "2.1"},
    cues={
        "typescript": LanguageCues(
            test_framework_primitives={
                "it", "test", "describe", "expect",
                "beforeEach", "afterEach", "beforeAll", "afterAll",
                "vi", "vitest",
            },
        ),
    },
)
