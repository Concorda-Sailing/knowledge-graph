"""Event-driven plugin — message queues and event buses.

Activates when a queue/event-bus library is in deps (kafka, rabbitmq,
nats, sqs, etc.). Contributes flow-shape cues for systems where entry
points are message handlers, not HTTP endpoints. Conservative scope at
v0: only contributes cues that don't depend on a yet-to-be-extracted
`kind=handler`. Extends naturally once handler classification lands.
"""
from kg.shared.plugins import Plugin, has_npm_dep, has_pypi_dep

from logigraph.plugins.base import LogigraphCues


def _detect(repo_path):
    return (
        has_npm_dep(repo_path, "amqplib")
        or has_npm_dep(repo_path, "kafkajs")
        or has_npm_dep(repo_path, "@aws-sdk/client-sqs")
        or has_npm_dep(repo_path, "nats")
        or has_npm_dep(repo_path, "bull")
        or has_npm_dep(repo_path, "bullmq")
        or has_pypi_dep(repo_path, "kafka-python")
        or has_pypi_dep(repo_path, "aio-pika")
        or has_pypi_dep(repo_path, "pika")
        or has_pypi_dep(repo_path, "celery")
        or has_pypi_dep(repo_path, "boto3")  # SQS via boto3
        or has_pypi_dep(repo_path, "nats-py")
    )


PLUGIN = Plugin(
    name="event-driven",
    detect=_detect,
    cues={"logigraph": LogigraphCues(
        entrypoint_kinds={"handler"},
        sink_kinds={"publisher"},
        headless_skip_kinds={"test"},
        kind_weights={
            "publisher": 1.0,
            "service": 0.65,
        },
    )},
)
