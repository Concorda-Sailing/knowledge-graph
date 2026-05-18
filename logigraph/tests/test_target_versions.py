"""Gating test — every framework logigraph plugin pins a version.

Same shape as the depgraph-side check in
`depgraph/tests/test_plugin_registry.py::test_every_framework_plugin_declares_target_versions`.
Without this gate, plugins drift silently and reviewers can't tell
which ones still match the current major.
"""
from __future__ import annotations

from logigraph.plugins import _discover_shipped_plugins


def test_every_framework_plugin_declares_target_versions():
    for p in _discover_shipped_plugins():
        if p.name.startswith("general:"):
            continue
        assert p.target_versions, (
            f"logigraph plugin {p.name!r} is missing target_versions; "
            f"every framework plugin must pin the version its cues were "
            f"authored against (e.g. target_versions={{\"next\": \"16.2\"}})"
        )
        for lib, ver in p.target_versions.items():
            assert lib and isinstance(lib, str)
            assert ver and isinstance(ver, str)
