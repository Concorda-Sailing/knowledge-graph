## Prediction (written before running extractor)

### Pattern
`if x: s = A() else: s = B(); s.do_work()` inside `run(x: bool)`.

### INTENTIONALLY PINNED WRONG BEHAVIOR

This fixture pins v0's walk-order-dependent assignment semantics.

### Analysis of ast.walk order

`ast.walk` is a BFS traversal. For the function body:
```
FunctionDef(run)
  body: [If, Return(s.do_work())]
```

`ast.walk` visits:
1. FunctionDef
2. If (child of FunctionDef body)
3. Return (child of FunctionDef body)
4. If.test (Name: x)
5. If.body[0] = Assign(s = A())   ← body branch
6. If.orelse[0] = Assign(s = B()) ← orelse branch
7. (Return's children)
...

Both assignments are visited. The last one to set `var_types["s"]` wins.

`If.body[0]` (s=A) is visited before `If.orelse[0]` (s=B) in ast.walk's BFS.

**Prediction: `var_types["s"] = B` after both Assigns are processed.**
→ `s.do_work()` resolves to `fixture::src.py::B.do_work` (wrong — the correct answer
depends on runtime control flow, not AST walk order).

Also: before any Assign, the for loop also processes the `ast.Call` for `A()` and `B()`.
Processing order within ast.walk mixes all of these... let me think more carefully.

Actually: `ast.walk` uses a deque and visits each node + all descendants. For Assign(s=A()):
- ast.walk visits the Assign node itself
- Then in the next iteration, its children: [Name(s, Store), Call(A)]
- The Assign's processing in `_attach_call_edges` outer loop: checks `isinstance(sub, ast.Assign)` → updates var_types.

So the outer loop `for sub in ast.walk(fn_node)` processes each node. When it hits
`Assign(s=A())`, it sets `var_types["s"] = A`. When it hits `Assign(s=B())`, it
overwrites to `var_types["s"] = B`. BFS visits body before orelse, so `A` first, `B` last.

**Final var_types["s"] = B. `s.do_work()` → B.do_work.**

Additionally:
- `A()` is a Call → emits `instantiates -> A`
- `B()` is a Call → emits `instantiates -> B`
- `s.do_work()` → `calls -> B.do_work` (wrong branch, but deterministic)

### WHY THIS IS PINNED WRONG
The correct behavior requires control-flow sensitivity: knowing that only ONE branch
executes at runtime. v0 uses ast.walk order which is a BFS artifact.
Future flow-sensitive pass should produce BOTH edges (for both branches) or model the join.
This fixture is the regression target for that future pass.

### Predicted edges from `run` (non-defines):
- `instantiates -> fixture::src.py::A` (exact) — from A()
- `instantiates -> fixture::src.py::B` (exact) — from B()
- `calls -> fixture::src.py::B.do_work` (exact) — WRONG per semantics, right per v0 walk order
