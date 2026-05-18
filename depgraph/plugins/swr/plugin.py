"""SWR plugin — Vercel's React data-fetching library.

Activates when `swr` is in npm deps. Contributes the canonical SWR
hooks so components using them get classified as hooks.

Doc references:
  https://swr.vercel.app/docs/api
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="swr",
    detect=lambda repo_path: has_npm_dep(repo_path, "swr"),
    target_versions={"swr": "2.2"},
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                "useSWR", "useSWRConfig", "useSWRInfinite", "useSWRMutation",
                "useSWRSubscription",
            },
        ),
    },
)
