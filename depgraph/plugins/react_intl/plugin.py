"""react-intl plugin (FormatJS).

Activates when `react-intl` is in npm deps. Contributes the canonical
i18n hook so components using `useIntl` get classified as hooks.

Doc references:
  https://formatjs.io/docs/react-intl/api#useintl-hook
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="react-intl",
    detect=lambda repo_path: has_npm_dep(repo_path, "react-intl"),
    cues={
        "typescript": LanguageCues(
            hook_call_names={"useIntl"},
        ),
    },
)
