"""factory.build_client dispatch."""
from __future__ import annotations

import pytest

from depgraph.lib.summarizer.anthropic_client import AnthropicLLMClient
from depgraph.lib.summarizer.config import ModelConfig
from depgraph.lib.summarizer.factory import build_client
from depgraph.lib.summarizer.openai_client import OpenAILLMClient


def test_build_openai_client():
    cfg = ModelConfig(name="x", spec="openai",
                       endpoint="http://x", model="m")
    assert isinstance(build_client(cfg), OpenAILLMClient)


def test_build_anthropic_client():
    cfg = ModelConfig(name="x", spec="anthropic",
                       endpoint="http://x", model="m")
    assert isinstance(build_client(cfg), AnthropicLLMClient)


def test_unknown_spec_raises():
    # ModelConfig.__init__ doesn't validate spec — only load_models does.
    # factory must catch the case anyway.
    cfg = ModelConfig(name="x", spec="not-a-spec",
                       endpoint="http://x", model="m")
    with pytest.raises(ValueError, match="unknown summarizer spec"):
        build_client(cfg)
