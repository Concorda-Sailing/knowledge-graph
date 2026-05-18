"""Always-on logigraph baseline plugin.

`general:logigraph` carries minimal cues that aren't framework-specific.
It always activates, mirrors the `general:python` / `general:typescript`
pattern in depgraph, and keeps the empty-active-set case (no detected
frameworks) from leaving the cue surface entirely empty.
"""
from logigraph.plugins.general.flow import PLUGIN as flow_plugin

__all__ = ["flow_plugin"]
