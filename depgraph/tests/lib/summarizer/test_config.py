"""Multi-model summarizer config parser."""
from __future__ import annotations

from pathlib import Path

import pytest

from depgraph.lib.summarizer.config import ModelConfig, load_models


def _write_toml(data_dir: Path, body: str) -> None:
    (data_dir / "nodes").mkdir(parents=True, exist_ok=True)
    (data_dir / "project.toml").write_text(body)


def test_load_models_empty_when_section_absent(tmp_path: Path) -> None:
    _write_toml(tmp_path, '[project]\nname = "x"\n')
    cfg = load_models(tmp_path)
    assert cfg.models == {}
    assert cfg.default_model is None


def test_load_models_parses_two_entries(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[project]
name = "x"

[summarizer]
default_model = "gemma-local"

[summarizer.models.gemma-local]
spec = "openai"
endpoint = "http://localhost:8080/v1"
model = "gemma-2-9b-it"
api_key_env = "GEMMA_LOCAL_KEY"

[summarizer.models.claude-haiku]
spec = "anthropic"
endpoint = "https://api.anthropic.com"
model = "claude-haiku-4-5"
api_key_env = "ANTHROPIC_API_KEY"
""")
    cfg = load_models(tmp_path)
    assert cfg.default_model == "gemma-local"
    assert set(cfg.models) == {"gemma-local", "claude-haiku"}
    g = cfg.models["gemma-local"]
    assert g.spec == "openai"
    assert g.endpoint == "http://localhost:8080/v1"
    assert g.model == "gemma-2-9b-it"
    assert g.api_key_env == "GEMMA_LOCAL_KEY"


def test_get_returns_default_when_no_name_passed(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer]
default_model = "claude"

[summarizer.models.gemma]
spec = "openai"
endpoint = "http://x"
model = "g"

[summarizer.models.claude]
spec = "anthropic"
endpoint = "http://y"
model = "c"
""")
    cfg = load_models(tmp_path)
    assert cfg.get().name == "claude"


def test_get_falls_back_to_first_model_when_no_default(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer.models.gemma]
spec = "openai"
endpoint = "http://x"
model = "g"
""")
    cfg = load_models(tmp_path)
    assert cfg.get().name == "gemma"


def test_get_named_raises_when_unknown(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer.models.gemma]
spec = "openai"
endpoint = "http://x"
model = "g"
""")
    cfg = load_models(tmp_path)
    with pytest.raises(KeyError, match="not configured"):
        cfg.get("missing")


def test_resolve_api_key_reads_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MYKEY", "secret")
    mc = ModelConfig(name="x", spec="openai", endpoint="http://x",
                     model="m", api_key_env="MYKEY")
    assert mc.resolve_api_key() == "secret"


def test_resolve_api_key_returns_none_when_var_unset() -> None:
    mc = ModelConfig(name="x", spec="openai", endpoint="http://x",
                     model="m", api_key_env="NEVER_SET_IN_TESTS")
    assert mc.resolve_api_key() is None


def test_resolve_api_key_returns_none_when_not_configured() -> None:
    """Local-only models with no api_key_env legitimately have no key."""
    mc = ModelConfig(name="x", spec="openai", endpoint="http://x", model="m")
    assert mc.resolve_api_key() is None


def test_invalid_spec_rejected(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer.models.weird]
spec = "made-up"
endpoint = "http://x"
model = "m"
""")
    with pytest.raises(ValueError, match="must be one of"):
        load_models(tmp_path)


def test_missing_endpoint_rejected(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer.models.broken]
spec = "openai"
model = "m"
""")
    with pytest.raises(ValueError, match="endpoint is required"):
        load_models(tmp_path)


def test_default_pointing_at_missing_model_rejected(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer]
default_model = "ghost"

[summarizer.models.real]
spec = "openai"
endpoint = "http://x"
model = "m"
""")
    with pytest.raises(ValueError, match="isn't declared"):
        load_models(tmp_path)


def test_endpoint_trailing_slash_stripped(tmp_path: Path) -> None:
    _write_toml(tmp_path, """
[summarizer.models.local]
spec = "openai"
endpoint = "http://localhost:8080/v1/"
model = "m"
""")
    cfg = load_models(tmp_path)
    assert cfg.models["local"].endpoint == "http://localhost:8080/v1"
