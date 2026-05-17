"""Hook classifier — use<Capital> functions that call a known React hook."""
from __future__ import annotations
import re

KIND = "hook"
_USE_PREFIX = re.compile(r"^use[A-Z]")


def classify(primitives, *, by_source, by_target, config, decisions_so_far):
    # Build the set of known external hook target ids from config cue names.
    # Convention: external::npm::react::<hookName>
    known_hook_externals = {f"external::npm::react::{n}" for n in config.hook_call_names}

    decisions = {}
    for p in primitives:
        if p["primitive"] != "function":
            continue
        name = p["name"].split(".")[-1]
        if not _USE_PREFIX.match(name):
            continue
        calls = [e for e in by_source.get(p["id"], []) if e["kind"] == "calls"]
        matching = [c for c in calls if c["target"] in known_hook_externals]
        if matching:
            decisions[p["id"]] = {
                "rule": "use_prefix_calls_hook",
                "evidence": matching,
            }
        # Transitive: calls another user-defined hook — handled by a future
        # second-pass in Task 5.7 once all hooks are classified.
    return decisions
