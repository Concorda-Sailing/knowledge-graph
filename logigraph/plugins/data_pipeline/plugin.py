"""Data-pipeline plugin — Airflow, Prefect, Dagster, etc.

Activates on common pipeline-orchestration deps. Contributes
entrypoint_kinds for the source/task pattern these systems use, sink
kinds for typical outputs, and skip rules so test fixtures don't
confuse headless-flow detection.
"""
from kg.shared.plugins import Plugin, has_pypi_dep

from logigraph.plugins.base import LogigraphCues


def _detect(repo_path):
    return (
        has_pypi_dep(repo_path, "apache-airflow")
        or has_pypi_dep(repo_path, "prefect")
        or has_pypi_dep(repo_path, "dagster")
        or has_pypi_dep(repo_path, "luigi")
    )


PLUGIN = Plugin(
    name="data-pipeline",
    detect=_detect,
    target_versions={
        "apache-airflow": "2.10",
        "prefect": "3.1",
        "dagster": "1.9",
        "luigi": "3.5",
    },
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"task", "stage", "source"},
        sink_kinds={"output", "sink"},
        headless_skip_kinds={"test"},
        kind_weights={
            "output": 1.0,
            "sink": 1.0,
            "stage": 0.85,
        },
    )},
)
