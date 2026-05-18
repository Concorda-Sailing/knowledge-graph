"""Agent loop tests — drive a fake client through tool-use turns."""
from __future__ import annotations

from typing import Optional

import pytest

from depgraph.lib.summarizer.agent import run_agent
from depgraph.lib.summarizer.base import BaseLLMClient
from depgraph.lib.summarizer.config import ModelConfig
from depgraph.lib.summarizer.types import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)


class FakeClient(BaseLLMClient):
    """Client whose `complete` returns successive scripted responses.

    Each call pops the next response off the script and records the
    messages it was given (so tests can assert on conversation shape).
    """

    def __init__(self, script: list[LLMResponse]):
        super().__init__(ModelConfig(name="fake", spec="openai",
                                       endpoint="http://x", model="m"))
        self._script = list(script)
        self.calls: list[dict] = []

    def complete(self, messages, *, tools=None, system=None,
                 max_tokens=None, temperature=0.2):
        self.calls.append({
            "messages": [m for m in messages],
            "tools": list(tools) if tools else None,
            "system": system,
        })
        if not self._script:
            raise RuntimeError("FakeClient script exhausted")
        return self._script.pop(0)


def test_one_shot_mode_no_tools() -> None:
    """tools=None bypasses the agent loop entirely."""
    client = FakeClient([
        LLMResponse(text="here's your summary", stop_reason="end_turn",
                    usage={"input_tokens": 5, "output_tokens": 3}),
    ])
    result = run_agent(client, user_prompt="summarize x")
    assert result.text == "here's your summary"
    assert result.turns == 1
    assert result.stop_reason == "end_turn"
    assert result.usage_totals == {"input_tokens": 5, "output_tokens": 3}
    # No tools were sent.
    assert client.calls[0]["tools"] is None


def test_tool_loop_one_call_then_final() -> None:
    """Model asks for a tool, agent runs handler, model returns final answer."""
    tool_def = ToolDefinition(name="read", description="", input_schema={"type": "object"})
    client = FakeClient([
        LLMResponse(text="", stop_reason="tool_use",
                    tool_calls=[ToolCall(id="c1", name="read", arguments={"k": "v"})]),
        LLMResponse(text="done", stop_reason="end_turn"),
    ])
    seen: list[dict] = []

    def read_handler(args):
        seen.append(args)
        return f"read got args={args}"

    result = run_agent(
        client, user_prompt="please",
        tools=[tool_def], tool_handlers={"read": read_handler},
    )
    assert result.text == "done"
    assert result.turns == 2
    assert seen == [{"k": "v"}]
    # Tools were sent on both turns.
    assert client.calls[0]["tools"] == [tool_def]
    assert client.calls[1]["tools"] == [tool_def]
    # Second turn includes the assistant tool_call + the tool result.
    second = client.calls[1]["messages"]
    assert second[1].role == "assistant"
    assert second[1].tool_calls[0].name == "read"
    assert second[2].role == "tool"
    assert second[2].tool_results[0].content == "read got args={'k': 'v'}"


def test_tool_handler_exception_becomes_is_error_result() -> None:
    """A raising handler must not crash the loop — the model is given the
    error text and decides what to do."""
    tool_def = ToolDefinition(name="bad", description="", input_schema={"type": "object"})
    client = FakeClient([
        LLMResponse(text="", stop_reason="tool_use",
                    tool_calls=[ToolCall(id="c1", name="bad", arguments={})]),
        LLMResponse(text="recovered", stop_reason="end_turn"),
    ])

    def bad_handler(args):
        raise ValueError("boom")

    result = run_agent(
        client, user_prompt="x",
        tools=[tool_def], tool_handlers={"bad": bad_handler},
    )
    assert result.text == "recovered"
    second = client.calls[1]["messages"]
    tr = second[2].tool_results[0]
    assert tr.is_error is True
    assert "ValueError" in tr.content


def test_unregistered_tool_name_returns_error_result() -> None:
    tool_def = ToolDefinition(name="known", description="", input_schema={"type": "object"})
    client = FakeClient([
        LLMResponse(text="", stop_reason="tool_use",
                    tool_calls=[ToolCall(id="c1", name="ghost", arguments={})]),
        LLMResponse(text="never mind", stop_reason="end_turn"),
    ])
    result = run_agent(
        client, user_prompt="x",
        tools=[tool_def], tool_handlers={"known": lambda a: "ok"},
    )
    assert result.text == "never mind"
    tr = client.calls[1]["messages"][2].tool_results[0]
    assert tr.is_error is True
    assert "ghost" in tr.content


def test_max_turns_exhausted_returns_max_turns_stop_reason() -> None:
    """A model that keeps asking for tools forever should bail at the cap."""
    tool_def = ToolDefinition(name="loop", description="", input_schema={"type": "object"})
    # Three tool-use responses; max_turns=2 means we bail after the second.
    script = [
        LLMResponse(text="", stop_reason="tool_use",
                    tool_calls=[ToolCall(id=f"c{i}", name="loop", arguments={})])
        for i in range(5)
    ]
    client = FakeClient(script)
    result = run_agent(
        client, user_prompt="x",
        tools=[tool_def], tool_handlers={"loop": lambda a: "tick"},
        max_turns=2,
    )
    assert result.stop_reason == "max_turns"
    assert result.turns == 2
    assert len(result.tool_calls_made) == 2


def test_usage_totals_summed_across_turns() -> None:
    tool_def = ToolDefinition(name="x", description="", input_schema={"type": "object"})
    client = FakeClient([
        LLMResponse(text="", stop_reason="tool_use",
                    tool_calls=[ToolCall(id="c1", name="x", arguments={})],
                    usage={"input_tokens": 10, "output_tokens": 4}),
        LLMResponse(text="done", stop_reason="end_turn",
                    usage={"input_tokens": 20, "output_tokens": 6}),
    ])
    result = run_agent(
        client, user_prompt="x",
        tools=[tool_def], tool_handlers={"x": lambda a: "y"},
    )
    assert result.usage_totals == {"input_tokens": 30, "output_tokens": 10}


def test_one_shot_passes_system_through() -> None:
    client = FakeClient([LLMResponse(text="ok", stop_reason="end_turn")])
    run_agent(client, user_prompt="x", system="be terse")
    assert client.calls[0]["system"] == "be terse"


def test_assistant_text_preserved_alongside_tool_calls() -> None:
    """Some specs (Anthropic) emit text + tool_use in the same turn. The
    agent must propagate both to the next request's history."""
    tool_def = ToolDefinition(name="read", description="", input_schema={"type": "object"})
    client = FakeClient([
        LLMResponse(text="let me check that", stop_reason="tool_use",
                    tool_calls=[ToolCall(id="c1", name="read", arguments={})]),
        LLMResponse(text="here it is", stop_reason="end_turn"),
    ])
    result = run_agent(
        client, user_prompt="x",
        tools=[tool_def], tool_handlers={"read": lambda a: "data"},
    )
    second_messages = client.calls[1]["messages"]
    assistant = second_messages[1]
    assert assistant.role == "assistant"
    assert assistant.content == "let me check that"
    assert assistant.tool_calls[0].id == "c1"
    assert result.text == "here it is"
