"""GrowthBook feature-flag plugin.

Activates when `@growthbook/growthbook-react` or `@growthbook/growthbook`
is in npm deps. Contributes the canonical feature-flag hooks so
components using `useFeature` / `useFeatureValue` / `useFeatureIsOn`
get classified as hooks.

Doc references:
  https://docs.growthbook.io/lib/react
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="growthbook",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "@growthbook/growthbook-react")
        or has_npm_dep(repo_path, "@growthbook/growthbook")
    ),
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                "useFeature", "useFeatureValue", "useFeatureIsOn",
                "useGrowthBook", "useExperiment",
            },
        ),
    },
)
