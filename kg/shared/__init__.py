"""Cross-graph shared helpers used by both depgraph and logigraph CLIs.

Lives outside both lib/cli/ packages to avoid the namespace-overlap
pitfall that Phase 3's tests/conftest.py works around (both lib/cli
packages share the unqualified name `lib`).
"""
