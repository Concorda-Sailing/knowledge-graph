"""Nuxt plugin — Vue-flavoured Next.js. Pages live under `pages/*.vue`;
composables (Nuxt's hook equivalent) live under `composables/`.
"""
from kg.shared.plugins import Plugin, has_npm_dep

from logigraph.plugins.base import LogigraphCues

PLUGIN = Plugin(
    name="nuxt",
    detect=lambda repo_path: has_npm_dep(repo_path, "nuxt"),
    cues={"logigraph": LogigraphCues(
        ui_entry_path_globs={
            "pages/**/*.vue",
            "src/pages/**/*.vue",
        },
        api_client_path_globs={
            "composables/**/*.ts", "composables/**/*.js",
            "src/composables/**/*.ts", "src/composables/**/*.js",
        },
    )},
)
