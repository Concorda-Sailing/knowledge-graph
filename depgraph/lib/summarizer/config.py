"""Multi-model summarizer config parsed from depgraph/project.toml.

Schema::

    [summarizer]
    default_model = "gemma-local"        # optional; first one wins if absent

    [summarizer.models.gemma-local]
    spec        = "openai"                # required: "openai" | "anthropic"
    endpoint    = "http://localhost:8080/v1"   # required
    model       = "gemma-2-9b-it"         # required
    api_key_env = "GEMMA_LOCAL_KEY"       # optional; if unset, no Authorization header
    timeout     = 120                     # optional, seconds
    max_tokens  = 4096                    # optional default for completions

    [summarizer.models.claude-haiku]
    spec        = "anthropic"
    endpoint    = "https://api.anthropic.com"
    model       = "claude-haiku-4-5"
    api_key_env = "ANTHROPIC_API_KEY"

Keys live in env vars, not in project.toml — `api_key_env` names which
var to read. Local-hosted endpoints (Ollama, vLLM) often need no key at
all, so omitting `api_key_env` is allowed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


_VALID_SPECS = {"openai", "anthropic"}


@dataclass(frozen=True)
class ModelConfig:
    """One [summarizer.models.<name>] entry, parsed and validated."""
    name: str
    spec: str                  # "openai" | "anthropic"
    endpoint: str              # base URL — clients append the spec's path
    model: str                 # model id passed to the API
    api_key_env: Optional[str] = None
    timeout: int = 120
    max_tokens: int = 4096
    # Reasoning-effort hint for models that expose it via the OpenAI-style
    # `reasoning_effort` parameter (e.g. xAI grok-4.3, OpenAI o-series).
    # Typical values: "low" | "medium" | "high". Omit for non-reasoning
    # models — most providers reject the field, some ignore it.
    reasoning_effort: Optional[str] = None

    def resolve_api_key(self) -> Optional[str]:
        """Return the API key from env, or None if not configured / unset.

        Local models (Ollama, vLLM with no auth) legitimately have no key.
        Cloud endpoints raise the key-missing concern only at call time —
        not here, because a partial config shouldn't trip CLI surfaces
        that don't actually call the model (e.g. `summarizer list`).
        """
        if not self.api_key_env:
            return None
        return os.environ.get(self.api_key_env) or None


@dataclass(frozen=True)
class SummarizerConfig:
    """The parsed `[summarizer]` block — all models + the default choice."""
    models: dict[str, ModelConfig]
    default_model: Optional[str]

    def get(self, name: Optional[str] = None) -> ModelConfig:
        """Resolve a model by name, or use the default."""
        if name:
            if name not in self.models:
                raise KeyError(
                    f"summarizer model {name!r} not configured; available: "
                    f"{sorted(self.models)}"
                )
            return self.models[name]
        if self.default_model and self.default_model in self.models:
            return self.models[self.default_model]
        # Fall back to first declared model (TOML preserves order).
        if self.models:
            return next(iter(self.models.values()))
        raise KeyError("no [summarizer.models.*] configured in project.toml")


def load_models(data_dir: Path) -> SummarizerConfig:
    """Read depgraph/project.toml and parse `[summarizer]` into typed config.

    Returns an empty SummarizerConfig when the block is absent, so callers
    can ask `if not cfg.models` to detect "feature not configured" without
    catching exceptions.
    """
    # Lazy import to keep config parsing usable from contexts that don't
    # otherwise want to drag in the wider depgraph config machinery.
    from depgraph.lib.config import load_project_config

    cfg = load_project_config(data_dir)
    section = (cfg.get("summarizer") or {})
    if not isinstance(section, dict):
        raise ValueError("project.toml [summarizer] must be a table")

    models_raw = section.get("models") or {}
    if not isinstance(models_raw, dict):
        raise ValueError("project.toml [summarizer.models] must be a table")

    models: dict[str, ModelConfig] = {}
    for name, entry in models_raw.items():
        if not isinstance(entry, dict):
            raise ValueError(
                f"project.toml [summarizer.models.{name}] must be a table"
            )
        spec = entry.get("spec")
        if spec not in _VALID_SPECS:
            raise ValueError(
                f"[summarizer.models.{name}].spec must be one of "
                f"{sorted(_VALID_SPECS)}, got {spec!r}"
            )
        endpoint = entry.get("endpoint")
        if not endpoint:
            raise ValueError(
                f"[summarizer.models.{name}].endpoint is required"
            )
        model = entry.get("model")
        if not model:
            raise ValueError(
                f"[summarizer.models.{name}].model is required"
            )
        models[name] = ModelConfig(
            name=name,
            spec=spec,
            endpoint=str(endpoint).rstrip("/"),
            model=str(model),
            api_key_env=entry.get("api_key_env"),
            timeout=int(entry.get("timeout") or 120),
            max_tokens=int(entry.get("max_tokens") or 4096),
            reasoning_effort=(
                str(entry["reasoning_effort"])
                if entry.get("reasoning_effort") is not None
                else None
            ),
        )

    default = section.get("default_model")
    if default is not None and not isinstance(default, str):
        raise ValueError("[summarizer].default_model must be a string")
    if default and default not in models:
        raise ValueError(
            f"[summarizer].default_model = {default!r} but that model "
            f"isn't declared; available: {sorted(models)}"
        )

    return SummarizerConfig(models=models, default_model=default)
