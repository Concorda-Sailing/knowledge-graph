"""OpenAI-spec client wire-format round-trip tests.

The client talks plain HTTP/JSON; we monkeypatch the network layer (`_post`)
and assert on the payload the client built + the LLMResponse it returned.
"""
from __future__ import annotations

import json

import pytest

from depgraph.lib.summarizer.config import ModelConfig
from depgraph.lib.summarizer.openai_client import OpenAILLMClient
from depgraph.lib.summarizer.types import LLMMessage, ToolCall, ToolDefinition, ToolResult


def _cfg(**overrides) -> ModelConfig:
    defaults = dict(
        name="local", spec="openai",
        endpoint="http://localhost:8080/v1",
        model="gemma-2-9b-it",
        api_key_env=None,
    )
    defaults.update(overrides)
    return ModelConfig(**defaults)


def _stub_post(captured: dict, response: dict):
    """Build a fake `_post` that records the request and returns `response`."""
    def fake(self, path, payload, *, headers):
        captured["path"] = path
        captured["payload"] = payload
        captured["headers"] = headers
        return response
    return fake


def test_oneshot_text_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    response = {
        "choices": [{
            "message": {"role": "assistant", "content": "hello back"},
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 12, "completion_tokens": 5},
    }
    monkeypatch.setattr(OpenAILLMClient, "_post", _stub_post(captured, response))

    c = OpenAILLMClient(_cfg())
    resp = c.complete([LLMMessage(role="user", content="hello")])

    assert captured["path"] == "/chat/completions"
    assert captured["payload"]["model"] == "gemma-2-9b-it"
    assert captured["payload"]["messages"] == [
        {"role": "user", "content": "hello"},
    ]
    assert resp.text == "hello back"
    assert resp.tool_calls == []
    assert resp.stop_reason == "end_turn"
    assert resp.usage == {"input_tokens": 12, "output_tokens": 5}


def test_system_prompt_inserted_at_front(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg())
    c.complete([LLMMessage(role="user", content="hi")], system="be terse")
    assert captured["payload"]["messages"][0] == {"role": "system", "content": "be terse"}


def test_authorization_header_when_api_key_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MYKEY", "sk-xyz")
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg(api_key_env="MYKEY"))
    c.complete([LLMMessage(role="user", content="x")])
    assert captured["headers"]["Authorization"] == "Bearer sk-xyz"


def test_no_authorization_header_when_local_unauthenticated(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg())  # no api_key_env
    c.complete([LLMMessage(role="user", content="x")])
    assert "Authorization" not in captured["headers"]


def test_tools_translated_to_functions_format(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg())
    tools = [ToolDefinition(
        name="read_source",
        description="Read source",
        input_schema={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    )]
    c.complete([LLMMessage(role="user", content="x")], tools=tools)
    assert captured["payload"]["tools"] == [{
        "type": "function",
        "function": {
            "name": "read_source",
            "description": "Read source",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
        },
    }]


def test_tool_choice_required_on_first_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg())
    tools = [ToolDefinition(name="read_source", description="", input_schema={"type": "object"})]
    c.complete([LLMMessage(role="user", content="x")], tools=tools)
    assert captured["payload"]["tool_choice"] == "required"


def test_tool_choice_auto_after_prior_tool_use(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg())
    tools = [ToolDefinition(name="read_source", description="", input_schema={"type": "object"})]
    history = [
        LLMMessage(role="user", content="x"),
        LLMMessage(
            role="assistant",
            tool_calls=[ToolCall(id="call_1", name="read_source", arguments={"path": "a.py"})],
        ),
        LLMMessage(role="tool", tool_results=[ToolResult(tool_call_id="call_1", content="…")]),
    ]
    c.complete(history, tools=tools)
    assert captured["payload"]["tool_choice"] == "auto"


def test_tool_call_response_parsed(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_42",
                    "type": "function",
                    "function": {
                        "name": "read_source",
                        "arguments": '{"repo": "api", "path": "x.py", "start_line": 1, "end_line": 5}',
                    },
                }],
            },
            "finish_reason": "tool_calls",
        }],
    }
    monkeypatch.setattr(OpenAILLMClient, "_post", _stub_post({}, response))
    c = OpenAILLMClient(_cfg())
    resp = c.complete([LLMMessage(role="user", content="x")], tools=[
        ToolDefinition(name="read_source", description="", input_schema={"type": "object"}),
    ])
    assert resp.stop_reason == "tool_use"
    assert len(resp.tool_calls) == 1
    tc = resp.tool_calls[0]
    assert tc.id == "call_42"
    assert tc.name == "read_source"
    assert tc.arguments == {"repo": "api", "path": "x.py", "start_line": 1, "end_line": 5}


def test_assistant_message_with_tool_calls_round_trips(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When the agent loop replays a prior tool-asking turn, it must serialize
    back to OpenAI's tool_calls array."""
    captured: dict = {}
    monkeypatch.setattr(
        OpenAILLMClient, "_post",
        _stub_post(captured, {"choices": [{"message": {"content": "done"}, "finish_reason": "stop"}]}),
    )
    c = OpenAILLMClient(_cfg())
    history = [
        LLMMessage(role="user", content="please read x"),
        LLMMessage(role="assistant", content="",
                   tool_calls=[ToolCall(id="call_1", name="read_source",
                                         arguments={"path": "x"})]),
        LLMMessage(role="tool",
                   tool_results=[ToolResult(tool_call_id="call_1", content="line1")]),
    ]
    c.complete(history, tools=[ToolDefinition(name="read_source", description="", input_schema={})])
    msgs = captured["payload"]["messages"]
    assistant_turn = next(m for m in msgs if m["role"] == "assistant")
    assert assistant_turn["tool_calls"][0]["id"] == "call_1"
    assert json.loads(assistant_turn["tool_calls"][0]["function"]["arguments"]) == {"path": "x"}
    tool_turn = next(m for m in msgs if m["role"] == "tool")
    assert tool_turn["tool_call_id"] == "call_1"
    assert tool_turn["content"] == "line1"


def test_malformed_tool_arguments_dont_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": "call_x",
                    "type": "function",
                    "function": {"name": "read_source", "arguments": "not json"},
                }],
            },
            "finish_reason": "tool_calls",
        }],
    }
    monkeypatch.setattr(OpenAILLMClient, "_post", _stub_post({}, response))
    c = OpenAILLMClient(_cfg())
    resp = c.complete([LLMMessage(role="user", content="x")], tools=[
        ToolDefinition(name="read_source", description="", input_schema={}),
    ])
    # Falls through to a stub args dict rather than raising.
    assert resp.tool_calls[0].arguments == {"_raw_arguments": "not json"}


def test_finish_reason_length_becomes_max_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    response = {"choices": [{"message": {"content": "trun"}, "finish_reason": "length"}]}
    monkeypatch.setattr(OpenAILLMClient, "_post", _stub_post({}, response))
    c = OpenAILLMClient(_cfg())
    resp = c.complete([LLMMessage(role="user", content="x")])
    assert resp.stop_reason == "max_tokens"
