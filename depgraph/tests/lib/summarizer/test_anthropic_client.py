"""Anthropic-spec client wire-format round-trip tests."""
from __future__ import annotations

import pytest

from depgraph.lib.summarizer.anthropic_client import AnthropicLLMClient
from depgraph.lib.summarizer.config import ModelConfig
from depgraph.lib.summarizer.types import LLMMessage, ToolCall, ToolDefinition, ToolResult


def _cfg(**overrides) -> ModelConfig:
    defaults = dict(
        name="claude", spec="anthropic",
        endpoint="https://api.anthropic.com",
        model="claude-haiku-4-5",
        api_key_env=None,
    )
    defaults.update(overrides)
    return ModelConfig(**defaults)


def _stub_post(captured: dict, response: dict):
    def fake(self, path, payload, *, headers):
        captured["path"] = path
        captured["payload"] = payload
        captured["headers"] = headers
        return response
    return fake


def test_oneshot_text_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    response = {
        "id": "msg_1",
        "role": "assistant",
        "content": [{"type": "text", "text": "hello back"}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 3},
    }
    monkeypatch.setattr(AnthropicLLMClient, "_post", _stub_post(captured, response))

    c = AnthropicLLMClient(_cfg())
    resp = c.complete([LLMMessage(role="user", content="hello")])

    assert captured["path"] == "/v1/messages"
    assert captured["payload"]["model"] == "claude-haiku-4-5"
    assert captured["payload"]["messages"] == [
        {"role": "user", "content": "hello"},
    ]
    assert resp.text == "hello back"
    assert resp.stop_reason == "end_turn"
    assert resp.usage == {"input_tokens": 10, "output_tokens": 3}


def test_system_carried_as_top_level_field(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        AnthropicLLMClient, "_post",
        _stub_post(captured, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}),
    )
    c = AnthropicLLMClient(_cfg())
    c.complete([LLMMessage(role="user", content="x")], system="be terse")
    assert captured["payload"]["system"] == "be terse"
    # And system is NOT in the messages array.
    assert all(m["role"] != "system" for m in captured["payload"]["messages"])


def test_x_api_key_header_when_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHRO_KEY", "sk-ant-xxx")
    captured: dict = {}
    monkeypatch.setattr(
        AnthropicLLMClient, "_post",
        _stub_post(captured, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}),
    )
    c = AnthropicLLMClient(_cfg(api_key_env="ANTHRO_KEY"))
    c.complete([LLMMessage(role="user", content="x")])
    assert captured["headers"]["x-api-key"] == "sk-ant-xxx"
    assert "anthropic-version" in captured["headers"]


def test_no_api_key_header_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        AnthropicLLMClient, "_post",
        _stub_post(captured, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}),
    )
    c = AnthropicLLMClient(_cfg())
    c.complete([LLMMessage(role="user", content="x")])
    assert "x-api-key" not in captured["headers"]


def test_tools_carry_input_schema(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        AnthropicLLMClient, "_post",
        _stub_post(captured, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}),
    )
    c = AnthropicLLMClient(_cfg())
    tools = [ToolDefinition(
        name="read_source",
        description="Read source",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
    )]
    c.complete([LLMMessage(role="user", content="x")], tools=tools)
    assert captured["payload"]["tools"] == [{
        "name": "read_source",
        "description": "Read source",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}},
    }]


def test_tool_use_response_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "id": "msg_2",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "let me check"},
            {"type": "tool_use",
             "id": "toolu_a",
             "name": "read_source",
             "input": {"path": "x.py"}},
        ],
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 20, "output_tokens": 5},
    }
    monkeypatch.setattr(AnthropicLLMClient, "_post", _stub_post({}, response))
    c = AnthropicLLMClient(_cfg())
    resp = c.complete([LLMMessage(role="user", content="x")], tools=[
        ToolDefinition(name="read_source", description="", input_schema={"type": "object"}),
    ])
    assert resp.text == "let me check"
    assert resp.stop_reason == "tool_use"
    assert len(resp.tool_calls) == 1
    tc = resp.tool_calls[0]
    assert tc.id == "toolu_a"
    assert tc.name == "read_source"
    assert tc.arguments == {"path": "x.py"}


def test_tool_result_translated_to_user_turn_with_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        AnthropicLLMClient, "_post",
        _stub_post(captured, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}),
    )
    c = AnthropicLLMClient(_cfg())
    history = [
        LLMMessage(role="user", content="please read"),
        LLMMessage(role="assistant", content="checking",
                   tool_calls=[ToolCall(id="toolu_a", name="read_source",
                                          arguments={"path": "x"})]),
        LLMMessage(role="tool",
                   tool_results=[
                       ToolResult(tool_call_id="toolu_a", content="line1"),
                   ]),
    ]
    c.complete(history, tools=[ToolDefinition(name="read_source", description="", input_schema={})])

    msgs = captured["payload"]["messages"]
    # Anthropic carries tool_result on a USER-role turn with tool_result blocks.
    last = msgs[-1]
    assert last["role"] == "user"
    assert last["content"][0]["type"] == "tool_result"
    assert last["content"][0]["tool_use_id"] == "toolu_a"
    assert last["content"][0]["content"] == "line1"


def test_is_error_flag_propagated(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        AnthropicLLMClient, "_post",
        _stub_post(captured, {"content": [{"type": "text", "text": "ok"}], "stop_reason": "end_turn"}),
    )
    c = AnthropicLLMClient(_cfg())
    history = [
        LLMMessage(role="user", content="please read"),
        LLMMessage(role="assistant", content="",
                   tool_calls=[ToolCall(id="toolu_b", name="read_source", arguments={})]),
        LLMMessage(role="tool",
                   tool_results=[
                       ToolResult(tool_call_id="toolu_b", content="boom", is_error=True),
                   ]),
    ]
    c.complete(history, tools=[ToolDefinition(name="read_source", description="", input_schema={})])
    last = captured["payload"]["messages"][-1]
    assert last["content"][0]["is_error"] is True
