"""Always-active logigraph baseline. Empty cues by design — frameworks
contribute the substance; this plugin's job is to be present so the
active set is never empty and downstream code can rely on a cues object
existing."""
from kg.shared.plugins import Plugin

from logigraph.plugins.base import LogigraphCues

PLUGIN = Plugin(
    name="general:logigraph",
    detect=lambda _path: True,
    cues={"logigraph": LogigraphCues()},
)
