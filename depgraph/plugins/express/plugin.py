"""Express plugin (TypeScript/JavaScript).

Activates when `express` is an npm dep. Contributes route-decorator cues
that drive endpoint classification — both the `app.X` (Express() instance)
and `router.X` (Router instance) chained-method patterns.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_npm_dep


def _routes(prefixes: list[str], verbs: list[str]) -> set[str]:
    return {f"{p}.{v}" for p in prefixes for v in verbs}


PLUGIN = Plugin(
    name="express",
    detect=lambda repo_path: has_npm_dep(repo_path, "express"),
    cues={
        "typescript": LanguageCues(
            route_decorators=_routes(
                ["app", "router"],
                ["get", "post", "put", "patch", "delete", "head", "options", "all", "use"],
            ),
        ),
    },
)
