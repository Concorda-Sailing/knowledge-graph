"""react-i18next + next-i18next plugin.

Activates when `react-i18next` (or its Next-specific wrapper
`next-i18next`) is in npm deps. Contributes the canonical i18n hook so
components using `useTranslation` get classified as hooks.

Doc references:
  https://react.i18next.com/latest/usetranslation-hook
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="react-i18next",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "react-i18next")
        or has_npm_dep(repo_path, "next-i18next")
    ),
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                "useTranslation", "useSSR",
            },
        ),
    },
)
