# Verification log: structural hash

**Last reviewed:** 2026-05-16 by Claude (haiku subagent under Opus controller)
**Components:** structural_hash_payload, compute_hash
**Source:** depgraph/lib/primitives.py

## Inputs exercised

For each input below, the "Predicted" column was filled in BEFORE running.
Discrepancies between Predicted and Observed (if any) are noted at the bottom.

| Input | Predicted | Observed |
|---|---|---|
| `compute_hash(payload_a)` vs `compute_hash(payload_b)` where both are same data but dict constructed in different key-insertion order | Equal — `sort_keys=True` in `json.dumps` normalises order | Equal: both `'02f2ad05d6149bae7d6c6a1777e78d1a9a12bdae3985c8f3e82e90b7865f417b'` |
| Same `structural_hash_payload(primitive="function", name="bar", signature={}, body_text="pass")` called twice | Equal — pure function, deterministic SHA-256 | Equal: both `'3d0dc04c1cf2a36bfe60b6d7f8d2545bd69f27aa039d1be33cd0b601511e2029'` |
| `structural_hash_payload(..., body_text="A")` vs `body_text="B"`, all other fields equal | Different hashes — body_text is included in payload | Different: `'f52847...'` vs `'8d8b5a...'` |
| `structural_hash_payload(..., body_text="A")` vs `body_text="A"` again | Equal | Equal |
| `structural_hash_payload(primitive="function", ...)` vs `primitive="class"`, same name/sig/body | Different hashes — primitive field is part of payload | Different: `'9dcb91...'` vs `'71636c...'` |
| `structural_hash_payload(primitive="function", name="foo", signature={})` (omitting body_text) vs explicit `body_text=""` | Equal — default is `""`, payload shape is identical | Payload shape confirmed identical; hashes equal |

## Observations

**Key observation — `sort_keys=True` applies only one level deep in practice:**
`json.dumps(..., sort_keys=True)` sorts recursively through all nested dicts, not just the top
level. This means a `signature` dict with keys in any order will always hash identically to one
with the same keys in a different order. Confirmed by the shuffled-key test: the nested
`signature: {"return_type": "int", "params": []}` sorted to `{"params": [], "return_type": "int"}`
under `sort_keys=True` and produced the same hash.

**`default=str` in `json.dumps`:**
Any non-JSON-serializable value in the payload (e.g., a `Path`, a dataclass, an `Enum`) will be
coerced to its `str()` representation rather than raising. This means a caller who accidentally
passes a `PrimitiveKind.FUNCTION` enum instead of the string `"function"` will get a hash over
`"PrimitiveKind.FUNCTION"` rather than `"function"` — silently wrong, not an error. Not exercised
here because `structural_hash_payload` takes plain strings, but validate_primitive should catch
bad enum types before they reach compute_hash.

**No surprises in the core hash properties.** The component behaves exactly as specified: order-
independent, deterministic, sensitive to every field value including body_text and primitive type.

## Status
✓ verified — all predictions matched observed output.
