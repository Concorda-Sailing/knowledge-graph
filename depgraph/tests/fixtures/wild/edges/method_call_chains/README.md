# method_call_chains

Tests v0 handling of chained method calls: `client.users.get().filter().first()`.

## Pattern
`run(client: Client)` calls `client.users.get().filter().first()`.

## Why tricky
Each call in the chain has a chained Attribute as its callee — `a.b.c()`.
The v0 extractor only handles single-hop `recv.method()` where `recv` is a Name node.
Chained calls (where the receiver is itself a Call or multi-hop Attribute) return `[]`.

## v0 behavior
- `run` emits zero calls edges for the chain (dropped, no edge at all).
- `Client.__init__` emits `instantiates -> UserSet` (bare Name call, resolves).
- `UserSet.get` emits `instantiates -> UserQuery` (bare Name call in return).

## Pinned behavior
Chained calls silently drop. Future work: emit `confidence: "unresolved_receiver"`
(per #53 Option A) for chained calls to preserve the information that a call
site exists.
