"""Web-API plugin — activates when any HTTP-server framework is in deps.

Contributes the cues that make logigraph's process-rank treat a corpus
as a request-response system: endpoint as flow entrypoint, model as
state-mutation sink, HTTP verb semantics for mutation filtering.
Activates broadly — express, NestJS, Fastify, Hapi (npm) plus FastAPI,
Django, Flask, Starlette (pypi). Each web framework's depgraph plugin
contributes the route-decorator cue strings; the logigraph plugin
contributes the flow-shape cues that depend on `kind=endpoint` /
`kind=model` having been emitted by classification.
"""
from kg.shared.plugins import Plugin, has_npm_dep, has_pypi_dep

from logigraph.plugins.base import LogigraphCues


def _detect(repo_path):
    return (
        has_npm_dep(repo_path, "express")
        or has_npm_dep(repo_path, "@nestjs/core")
        or has_npm_dep(repo_path, "fastify")
        or has_npm_dep(repo_path, "@hapi/hapi")
        or has_npm_dep(repo_path, "koa")
        or has_pypi_dep(repo_path, "fastapi")
        or has_pypi_dep(repo_path, "django")
        or has_pypi_dep(repo_path, "flask")
        or has_pypi_dep(repo_path, "starlette")
        or has_pypi_dep(repo_path, "sanic")
    )


PLUGIN = Plugin(
    name="web-api",
    detect=_detect,
    target_versions={
        "express": "4.21",
        "@nestjs/core": "10.4",
        "fastify": "5.1",
        "@hapi/hapi": "21.3",
        "koa": "2.15",
        "fastapi": "0.115",
        "django": "5.1",
        "flask": "3.0",
        "starlette": "0.41",
        "sanic": "24.6",
    },
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"endpoint"},
        sink_kinds={"model"},
        mutation_methods={"POST", "PUT", "DELETE", "PATCH"},
        headless_skip_kinds={
            "endpoint", "component", "test", "hook", "schema", "model",
        },
        kind_weights={
            "model": 1.0,
            "hook": 0.85,
            "service": 0.65,
            "schema": 0.45,
        },
        test_path_globs={
            "**/tests/**", "**/*.test.ts", "**/*.test.tsx",
            "**/*.spec.ts", "**/*.spec.tsx",
            "**/test_*.py", "**/*_test.py",
        },
    )},
)
