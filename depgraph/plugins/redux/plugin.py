"""Redux + react-redux plugin.

Activates when either `redux` or `react-redux` is in npm deps.
Contributes the canonical react-redux hooks to `hook_call_names` so
components using `useSelector` / `useDispatch` / `useStore` get
classified as hooks instead of plain functions.

Doc references:
  https://react-redux.js.org/api/hooks
"""
from kg.shared.plugins import Plugin, has_npm_dep

from depgraph.lib.classification.config import LanguageCues

PLUGIN = Plugin(
    name="redux",
    detect=lambda repo_path: (
        has_npm_dep(repo_path, "react-redux") or has_npm_dep(repo_path, "redux")
    ),
    target_versions={"react-redux": "9.1", "redux": "5.0"},
    cues={
        "typescript": LanguageCues(
            hook_call_names={
                "useSelector", "useDispatch", "useStore",
            },
        ),
    },
)
