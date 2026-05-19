"""The tool-use agent loop.

`run_agent` drives a multi-turn conversation: send → receive → if the
model asked for tools, execute them and send the results → repeat until
the model returns an `end_turn` or the turn cap is hit.

Stays small on purpose. The tool execution is plain Python (no eval, no
RPC machinery): each tool is a function with a known schema and the
caller supplies the implementations.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from depgraph.lib.summarizer.base import BaseLLMClient
from depgraph.lib.summarizer.types import (
    LLMMessage,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


logger = logging.getLogger("depgraph.summarizer.agent")


# A ToolHandler is a plain callable that takes the model's `arguments`
# dict and returns the text to send back. Raise on error and the agent
# loop will translate that into an is_error=True ToolResult.
ToolHandler = Callable[[dict], str]


@dataclass
class AgentResult:
    """Final outcome of an agent run."""
    text: str                                     # the model's final reply
    turns: int                                    # turns consumed (>=1)
    stop_reason: str                              # last stop_reason
    tool_calls_made: list[ToolCall] = field(default_factory=list)
    usage_totals: dict[str, int] = field(default_factory=dict)


def run_agent(
    client: BaseLLMClient,
    *,
    user_prompt: str,
    system: Optional[str] = None,
    tools: Optional[list[ToolDefinition]] = None,
    tool_handlers: Optional[dict[str, ToolHandler]] = None,
    max_turns: int = 64,
    temperature: float = 0.2,
) -> AgentResult:
    """Drive a tool-use conversation to completion.

    If `tools` is None, runs in one-shot mode: send the prompt, get back
    the text. Otherwise loop: every assistant turn that asks for tools is
    answered with the corresponding tool_handler(args) outputs.

    `max_turns` caps how many round-trips we'll make even if the model
    keeps asking for tools — guards against pathological tool-use loops.
    """
    handlers = dict(tool_handlers or {})
    if tools is None:
        # One-shot path.
        resp = client.complete(
            [LLMMessage(role="user", content=user_prompt)],
            system=system, temperature=temperature,
        )
        return AgentResult(
            text=resp.text,
            turns=1,
            stop_reason=resp.stop_reason,
            usage_totals=dict(resp.usage),
        )

    messages: list[LLMMessage] = [LLMMessage(role="user", content=user_prompt)]
    tool_calls_made: list[ToolCall] = []
    usage_totals: dict[str, int] = {}

    for turn in range(1, max_turns + 1):
        resp = client.complete(
            messages,
            tools=tools,
            system=system,
            temperature=temperature,
        )
        for k, v in (resp.usage or {}).items():
            usage_totals[k] = usage_totals.get(k, 0) + v

        if resp.stop_reason != "tool_use" or not resp.tool_calls:
            return AgentResult(
                text=resp.text,
                turns=turn,
                stop_reason=resp.stop_reason,
                tool_calls_made=tool_calls_made,
                usage_totals=usage_totals,
            )

        # Record the assistant turn that requested tools so the next
        # request carries it. Spec clients put tool_calls onto the
        # assistant turn (OpenAI) or as content blocks on it (Anthropic);
        # our normalized form puts them on the LLMMessage.tool_calls list.
        messages.append(LLMMessage(
            role="assistant",
            content=resp.text,
            tool_calls=list(resp.tool_calls),
        ))
        tool_calls_made.extend(resp.tool_calls)

        results: list[ToolResult] = []
        for call in resp.tool_calls:
            handler = handlers.get(call.name)
            if handler is None:
                results.append(ToolResult(
                    tool_call_id=call.id,
                    content=(
                        f"error: tool {call.name!r} not registered; "
                        f"available: {sorted(handlers)}"
                    ),
                    is_error=True,
                ))
                continue
            try:
                content = handler(call.arguments)
            except Exception as e:  # broad on purpose — feed back to model
                logger.warning("tool %s raised: %s", call.name, e)
                content = f"error: {type(e).__name__}: {e}"
                results.append(ToolResult(
                    tool_call_id=call.id, content=content, is_error=True,
                ))
                continue
            results.append(ToolResult(
                tool_call_id=call.id, content=content, is_error=False,
            ))
        messages.append(LLMMessage(role="tool", tool_results=results))

    # max_turns exhausted while the model was still calling tools.
    return AgentResult(
        text="",
        turns=max_turns,
        stop_reason="max_turns",
        tool_calls_made=tool_calls_made,
        usage_totals=usage_totals,
    )
