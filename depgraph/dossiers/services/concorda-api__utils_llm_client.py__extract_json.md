---
node_id: concorda-api::utils/llm_client.py::extract_json
node_kind: service
feature: null
last_reviewed: 2026-05-10
last_reviewed_against_hash: 5a0fdcca33910aed66c039782d954f3b885d3ffe8830e2635248a741d5a055e3
status: current
---

# extract_json

## Purpose

The utility for sanitizing and parsing LLM-generated strings into Python dictionaries. It provides a robust fallback mechanism for when an LLM returns text surrounding a JSON block (e.g., markdown code fences or conversational filler) instead of a raw JSON string. Use this instead of a naked `json.loads()` when the input source is a non-deterministic LLM completion.

## Invariants

- **Input is a raw string** from an LLM completion.
- **Returns a `dict`** representing the parsed JSON object.
- **Throws `json.JSONDecodeError`** if no valid JSON structure (including nested braces) can be identified.
- **Follows a three-stage fallback**: direct parse $\rightarrow$ markdown fence extraction $\rightarrow$ brace-counting heuristic.

## Gotchas

- **Heuristic depth failure**: The brace-counting logic (lines 158-164) relies on a balanced `depth` counter. If an LLM produces a malformed string with unmatched braces outside the primary object, the `json.loads` call may fail or capture an incomplete segment.
- **Regex dependency**: The markdown extraction (line 148) specifically looks for ` ```(?:json)? ` fences. If the LLM uses a different syntax or non-standard whitespace, the regex may fail to capture the block.

## Cross-cutting concerns

- **Auth**: none
- **Websocket**: none
- **Audit**: none
- **Rate limit**: none
- **Side effects**: none

## External consumers

None known.
