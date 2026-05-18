"""FastAPI plugin.

Activates when `fastapi` is a Python dependency. Contributes the route-
decorator cues that drive endpoint classification — both `app.X` (the
FastAPI() instance pattern) and `router.X` (the APIRouter pattern). The
HTTP verbs covered match what FastAPI accepts.
"""
from depgraph.lib.classification.config import LanguageCues
from kg.shared.plugins import Plugin, has_pypi_dep


def _routes(prefixes: list[str], verbs: list[str]) -> set[str]:
    return {f"{p}.{v}" for p in prefixes for v in verbs}


PLUGIN = Plugin(
    name="fastapi",
    detect=lambda repo_path: has_pypi_dep(repo_path, "fastapi"),
    cues={
        "python": LanguageCues(
            route_decorators=_routes(
                ["app", "router"],
                ["get", "post", "put", "patch", "delete", "head", "options"],
            ),
        ),
    },
)
