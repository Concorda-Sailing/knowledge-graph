# Verification log: wildcard_import_py

## Pre-read prediction

Without the fix: `from helpers import *` produces `imports → fixture::helpers.py`
with `confidence="exact"`, `local_binding="*"`. The "exact" lies and the
binding is useless.

With the fix: same target, `confidence="fuzzy"`, `via="wildcard_import"`,
no `local_binding` key.

## Prediction vs expected.json

Matches. One edge, fuzzy, module-level.

## Notes

The `util_a()` and `util_b()` call sites inside `use_them` emit no `calls`
edges — wildcard-import bindings aren't propagated to the calls pass's
local-name map. The reads/calls reachability gap is the deliberate v0
trade-off documented in README.md.
