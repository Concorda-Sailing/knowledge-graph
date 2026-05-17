"""Unit tests for `_ts_node_env`: the env-shaping helper for the tsx
subprocess that runs the TypeScript extractor.

Real-world web apps (~hundreds of source files) exhaust ts-morph at
Node's default ~2GB heap; the helper raises the floor with
--max-old-space-size=4096 while deferring to anything the caller has
already set in NODE_OPTIONS.
"""
from __future__ import annotations

from depgraph.lib.cli.regen import _DEFAULT_TS_HEAP_MB, _ts_node_env


def test_sets_heap_when_node_options_unset():
    env = _ts_node_env({"PATH": "/usr/bin"})
    assert env["NODE_OPTIONS"] == f"--max-old-space-size={_DEFAULT_TS_HEAP_MB}"
    assert env["PATH"] == "/usr/bin"


def test_appends_heap_to_existing_node_options():
    env = _ts_node_env({"NODE_OPTIONS": "--enable-source-maps"})
    assert env["NODE_OPTIONS"] == (
        f"--enable-source-maps --max-old-space-size={_DEFAULT_TS_HEAP_MB}"
    )


def test_respects_user_supplied_heap():
    env = _ts_node_env({"NODE_OPTIONS": "--max-old-space-size=8192"})
    assert env["NODE_OPTIONS"] == "--max-old-space-size=8192"


def test_respects_user_supplied_heap_among_other_flags():
    env = _ts_node_env({
        "NODE_OPTIONS": "--enable-source-maps --max-old-space-size=1024 --no-warnings",
    })
    assert env["NODE_OPTIONS"] == (
        "--enable-source-maps --max-old-space-size=1024 --no-warnings"
    )


def test_does_not_mutate_input_env():
    base = {"NODE_OPTIONS": "--enable-source-maps"}
    _ts_node_env(base)
    assert base == {"NODE_OPTIONS": "--enable-source-maps"}
