"""Normalized message / tool / response types shared by both clients.

The OpenAI and Anthropic wire formats differ enough that translating
through a neutral middle layer is cheaper than special-casing every
caller. Each client converts to-and-from these types at the network edge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolDefinition:
    """A tool the model can call.

    `input_schema` is a JSON Schema object describing the call arguments;
    both specs accept JSON Schema (Anthropic calls the field `input_schema`,
    OpenAI calls it `parameters`).
    """
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class ToolCall:
    """A tool invocation requested by the model.

    `id` is the call id assigned by the model — tool results must echo it
    back so the model can match them up across multi-tool turns.
    `arguments` is the parsed JSON object (model-provided args).
    """
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of executing a tool the model called.

    `content` is the text payload returned to the model.
    `is_error` signals that the tool failed (the model is expected to
    course-correct rather than re-run the same call).
    """
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class LLMMessage:
    """One turn in the conversation.

    `role` is one of: "user", "assistant", "tool".
    For "user" / "assistant" turns, `content` is plain text. For "tool"
    turns, `tool_results` carries the executed-tool payloads.
    Assistant turns that asked for tools also carry `tool_calls`.
    """
    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


@dataclass
class LLMResponse:
    """One model reply.

    `text` is the assistant's text output (may be empty if the model only
    asked for tools).
    `tool_calls` is the list of tool calls the model wants to make.
    `stop_reason` is a normalized string: "end_turn" (final answer),
    "tool_use" (asking for tools), "max_tokens", or "other".
    `usage` carries token counts when the API returns them.
    """
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    usage: dict[str, int] = field(default_factory=dict)
