"""Abstract LLM client + the small HTTP helper both spec clients share.

Each spec subclass converts to/from the normalized `LLMMessage` /
`LLMResponse` types in `types.py`. Network I/O goes through urllib
(stdlib only — no third-party HTTP dep) so monkeypatching in tests is a
one-liner.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Optional

from depgraph.lib.summarizer.config import ModelConfig
from depgraph.lib.summarizer.types import LLMMessage, LLMResponse, ToolDefinition


class LLMHTTPError(RuntimeError):
    """HTTP-level failure from the LLM endpoint.

    `status` is the HTTP status when known; 0 for transport errors
    (DNS, refused connection, etc.). `body` carries the response text
    (truncated) for diagnostics.
    """

    def __init__(self, status: int, body: str, hint: str = ""):
        self.status = status
        self.body = body
        msg = f"LLM HTTP {status}: {body[:400]}"
        if hint:
            msg = f"{msg}\nhint: {hint}"
        super().__init__(msg)


def _post_json(
    url: str,
    payload: dict,
    *,
    headers: dict[str, str],
    timeout: int,
) -> dict:
    """POST a JSON body and parse the JSON response.

    Both 4xx and 5xx are surfaced as LLMHTTPError so the caller can decide
    whether to retry / fall back. The stdlib `urlopen` raises on >=400 —
    we catch HTTPError to read the body before re-raising as our own type.
    """
    data = json.dumps(payload).encode("utf-8")
    # Set a real User-Agent: Cloudflare-fronted providers (Groq, sometimes
    # OpenAI) block the stdlib default "Python-urllib/X.Y" UA with HTTP
    # 403 / error 1010. Identifying as the framework satisfies the WAF
    # without pretending to be a browser. Caller-provided UA wins.
    final_headers = {
        "Content-Type": "application/json",
        "User-Agent": "knowledge-graph-depgraph/0.1 (+https://github.com/Concorda-Sailing/knowledge-graph)",
        **headers,
    }
    req = urllib.request.Request(
        url,
        data=data,
        headers=final_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise LLMHTTPError(e.code, body) from e
    except urllib.error.URLError as e:
        raise LLMHTTPError(0, str(e.reason)) from e
    except json.JSONDecodeError as e:
        raise LLMHTTPError(200, f"non-JSON response: {e}") from e


class BaseLLMClient(ABC):
    """Common surface for both spec clients.

    Subclasses implement `complete` against their wire format. Callers
    only see normalized types — no leakage of OpenAI vs Anthropic shapes.
    """

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        *,
        tools: Optional[list[ToolDefinition]] = None,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Send a completion request and return the model's reply.

        `messages` is the full conversation so far. `tools` is the tool
        catalog the model may call. `system` is the system prompt.
        `max_tokens` defaults to the model config's max_tokens.
        """
        ...

    # Subclasses share these helpers; they're not abstract.

    def _resolved_max_tokens(self, override: Optional[int]) -> int:
        return override if override is not None else self.cfg.max_tokens

    def _post(self, path: str, payload: dict, *, headers: dict[str, str]) -> dict:
        url = f"{self.cfg.endpoint}{path}"
        return _post_json(url, payload, headers=headers, timeout=self.cfg.timeout)
