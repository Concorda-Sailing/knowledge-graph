"""External LLM summarizer — clients, tools, and the agent loop that
drives dossier drafting on local or cloud models.

Two wire formats are supported natively (no third-party SDKs):
  - OpenAI-spec  (vLLM, Ollama, llama.cpp `server`, OpenAI/Azure, ...)
  - Anthropic-spec (Anthropic API, any future endpoint matching it)

Per-model config lives in `depgraph/project.toml::[summarizer.models.*]`;
each model entry declares its spec, endpoint, model name, and (optionally)
the env var holding the API key. See `config.load_models`.

Public exports here are the things callers reach for: the typed message /
tool / response dataclasses, the abstract client, the agent loop, the
factory, and the built-in tool registry.
"""
from depgraph.lib.summarizer.agent import AgentResult, run_agent
from depgraph.lib.summarizer.base import BaseLLMClient
from depgraph.lib.summarizer.config import ModelConfig, SummarizerConfig, load_models
from depgraph.lib.summarizer.factory import build_client
from depgraph.lib.summarizer.tools import (
    ToolHandler,
    builtin_tool_handlers,
    builtin_tool_definitions,
)
from depgraph.lib.summarizer.types import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
    ToolResult,
)

__all__ = [
    "AgentResult",
    "BaseLLMClient",
    "LLMMessage",
    "LLMResponse",
    "ModelConfig",
    "SummarizerConfig",
    "ToolCall",
    "ToolDefinition",
    "ToolHandler",
    "ToolResult",
    "build_client",
    "builtin_tool_definitions",
    "builtin_tool_handlers",
    "load_models",
    "run_agent",
]
