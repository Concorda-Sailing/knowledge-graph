"""Anthropic Messages API wire format.

Endpoint path used: `<endpoint>/v1/messages`. The Anthropic spec carries
the system prompt as a top-level `system` field (not a message turn),
and represents tool calls / results as content blocks rather than
separate roles.

This client is also compatible with Anthropic-spec proxies and any
self-hosted endpoint that implements the same shape.
"""
from __future__ import annotations

from typing import Optional

from depgraph.lib.summarizer.base import BaseLLMClient
from depgraph.lib.summarizer.types import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)


_STOP_MAP = {
    "end_turn": "end_turn",
    "tool_use": "tool_use",
    "max_tokens": "max_tokens",
    "stop_sequence": "end_turn",
}

# Anthropic version pin used as the API version header. Updating this is a
# deliberate change — keep it boring; pre-2024 versions don't speak the
# tool_use content-block format we rely on.
_ANTHROPIC_VERSION = "2023-06-01"


class AnthropicLLMClient(BaseLLMClient):

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        wire_messages = _to_anthropic_messages(messages)
        payload: dict = {
            "model": self.cfg.model,
            "messages": wire_messages,
            "max_tokens": self._resolved_max_tokens(max_tokens),
            "temperature": temperature,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = [_tool_to_anthropic(t) for t in tools]

        headers: dict[str, str] = {"anthropic-version": _ANTHROPIC_VERSION}
        key = self.cfg.resolve_api_key()
        if key:
            headers["x-api-key"] = key

        raw = self._post("/v1/messages", payload, headers=headers)
        return _from_anthropic_response(raw)


def _to_anthropic_messages(messages: list[LLMMessage]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if m.role == "user":
            out.append({"role": "user", "content": m.content})
        elif m.role == "assistant":
            blocks: list[dict] = []
            if m.content:
                blocks.append({"type": "text", "text": m.content})
            for tc in m.tool_calls:
                blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            out.append({"role": "assistant", "content": blocks})
        elif m.role == "tool":
            blocks = [
                {
                    "type": "tool_result",
                    "tool_use_id": r.tool_call_id,
                    "content": r.content,
                    **({"is_error": True} if r.is_error else {}),
                }
                for r in m.tool_results
            ]
            # Anthropic carries tool_result blocks on a user turn.
            out.append({"role": "user", "content": blocks})
        else:
            raise ValueError(f"unsupported message role: {m.role!r}")
    return out


def _tool_to_anthropic(t: ToolDefinition) -> dict:
    return {
        "name": t.name,
        "description": t.description,
        "input_schema": t.input_schema,
    }


def _from_anthropic_response(raw: dict) -> LLMResponse:
    blocks = raw.get("content") or []
    text_parts: list[str] = []
    tool_calls: list[ToolCall] = []
    for b in blocks:
        bt = b.get("type")
        if bt == "text":
            text_parts.append(b.get("text") or "")
        elif bt == "tool_use":
            tool_calls.append(ToolCall(
                id=b.get("id") or "",
                name=b.get("name") or "",
                arguments=b.get("input") or {},
            ))
    text = "".join(text_parts)
    stop_reason = _STOP_MAP.get(raw.get("stop_reason") or "", "other")
    usage_raw = raw.get("usage") or {}
    usage = {
        "input_tokens": int(usage_raw.get("input_tokens") or 0),
        "output_tokens": int(usage_raw.get("output_tokens") or 0),
    }
    return LLMResponse(
        text=text,
        tool_calls=tool_calls,
        stop_reason=stop_reason,
        usage=usage,
    )
