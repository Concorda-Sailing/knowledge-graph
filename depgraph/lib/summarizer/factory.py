"""Pick the right client class based on a ModelConfig's `spec` field."""
from __future__ import annotations

from depgraph.lib.summarizer.anthropic_client import AnthropicLLMClient
from depgraph.lib.summarizer.base import BaseLLMClient
from depgraph.lib.summarizer.config import ModelConfig
from depgraph.lib.summarizer.openai_client import OpenAILLMClient


_CLIENTS: dict[str, type[BaseLLMClient]] = {
    "openai": OpenAILLMClient,
    "anthropic": AnthropicLLMClient,
}


def build_client(cfg: ModelConfig) -> BaseLLMClient:
    """Return an instance of the spec-appropriate client class."""
    try:
        klass = _CLIENTS[cfg.spec]
    except KeyError as e:
        raise ValueError(
            f"unknown summarizer spec {cfg.spec!r}; supported: {sorted(_CLIENTS)}"
        ) from e
    return klass(cfg)
