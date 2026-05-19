"""OpenAI Chat Completions wire format.

Same spec is spoken by vLLM, Ollama (via `/v1/chat/completions`),
llama.cpp's `server`, LM Studio, Together, OpenRouter (when used as a
direct endpoint), and Azure OpenAI. Translating to/from our normalized
types happens at the network edge.

Path used: `<endpoint>/chat/completions` — `endpoint` should include the
`/v1` suffix when the provider requires it, mirroring the OpenAI client
configuration convention.
"""
from __future__ import annotations

import json
from typing import Optional

from depgraph.lib.summarizer.base import BaseLLMClient
from depgraph.lib.summarizer.types import (
    LLMMessage,
    LLMResponse,
    ToolCall,
    ToolDefinition,
)


_STOP_MAP = {
    "stop": "end_turn",
    "tool_calls": "tool_use",
    "function_call": "tool_use",  # legacy
    "length": "max_tokens",
}


class OpenAILLMClient(BaseLLMClient):

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        wire_messages = _to_openai_messages(messages, system=system)
        payload: dict = {
            "model": self.cfg.model,
            "messages": wire_messages,
            "max_tokens": self._resolved_max_tokens(max_tokens),
            "temperature": temperature,
        }
        if self.cfg.reasoning_effort:
            # OpenAI-spec field for reasoning models (xAI grok-4.3, OpenAI
            # o-series). Providers that don't support it generally either
            # ignore the field or return a 400; configure it only for
            # models known to honor it.
            payload["reasoning_effort"] = self.cfg.reasoning_effort
        if tools:
            payload["tools"] = [_tool_to_openai(t) for t in tools]
            # Force at least one tool call on the first agent-loop turn:
            # when no prior assistant turn carries tool_calls, the model
            # has not yet consulted any tool, and Granite (in particular)
            # otherwise drafts confidently from priors instead of calling
            # the registered tools. After the first tool round-trip the
            # follow-up turns revert to "auto" so the model can decide
            # when it has enough evidence to write the final response.
            prior_tool_use = any(
                m.role == "assistant" and m.tool_calls for m in messages
            )
            payload["tool_choice"] = "auto" if prior_tool_use else "required"

        headers: dict[str, str] = {}
        key = self.cfg.resolve_api_key()
        if key:
            headers["Authorization"] = f"Bearer {key}"

        raw = self._post("/chat/completions", payload, headers=headers)
        return _from_openai_response(raw)


def _to_openai_messages(
    messages: list[LLMMessage], *, system: Optional[str]
) -> list[dict]:
    out: list[dict] = []
    if system:
        out.append({"role": "system", "content": system})
    for m in messages:
        if m.role == "user":
            out.append({"role": "user", "content": m.content})
        elif m.role == "assistant":
            entry: dict = {"role": "assistant", "content": m.content or None}
            if m.tool_calls:
                entry["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in m.tool_calls
                ]
            out.append(entry)
        elif m.role == "tool":
            # OpenAI requires one message per tool_result, with tool_call_id.
            for r in m.tool_results:
                out.append({
                    "role": "tool",
                    "tool_call_id": r.tool_call_id,
                    "content": r.content,
                })
        else:
            raise ValueError(f"unsupported message role: {m.role!r}")
    return out


def _tool_to_openai(t: ToolDefinition) -> dict:
    return {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": t.input_schema,
        },
    }


def _extract_text_from_content(content) -> str:
    """OpenAI-compatible servers return `message.content` as either a
    plain string (most providers) or a list of typed blocks (Mistral's
    Magistral reasoning model and similar). For block lists, keep the
    `text`-type blocks and drop `thinking`-type blocks — the reasoning
    trace doesn't belong in the dossier body. Unknown block types are
    skipped to stay forward-compatible."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            btype = block.get("type")
            if btype == "text":
                parts.append(block.get("text") or "")
            # Skip "thinking", "image_url", and any other non-text blocks.
        return "".join(parts)
    # Unknown shape — best-effort stringify rather than crash.
    return str(content)


def _from_openai_response(raw: dict) -> LLMResponse:
    choices = raw.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenAI response had no choices: {raw}")
    choice = choices[0]
    msg = choice.get("message") or {}
    text = _extract_text_from_content(msg.get("content"))
    tool_calls: list[ToolCall] = []
    for tc in (msg.get("tool_calls") or []):
        fn = tc.get("function") or {}
        args_raw = fn.get("arguments") or "{}"
        try:
            args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
        except json.JSONDecodeError:
            # Model occasionally emits malformed JSON; surface as empty
            # rather than crashing the agent loop — the loop can report
            # the bad call back to the model on the next turn.
            args = {"_raw_arguments": args_raw}
        tool_calls.append(ToolCall(
            id=tc.get("id") or "",
            name=fn.get("name") or "",
            arguments=args,
        ))
    finish = choice.get("finish_reason") or "stop"
    stop_reason = _STOP_MAP.get(finish, "other")
    # OpenAI returns end_turn-style "stop" even when tool_calls are present
    # in some implementations; promote to "tool_use" in that case.
    if tool_calls and stop_reason != "max_tokens":
        stop_reason = "tool_use"
    usage_raw = raw.get("usage") or {}
    usage = {
        "input_tokens": int(usage_raw.get("prompt_tokens") or 0),
        "output_tokens": int(usage_raw.get("completion_tokens") or 0),
    }
    return LLMResponse(
        text=text,
        tool_calls=tool_calls,
        stop_reason=stop_reason,
        usage=usage,
    )
