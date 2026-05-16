# conditional_rebinding

Tests v0's walk-order-dependent behavior on conditional variable rebinding.

## Pattern
`if x: s = A() else: s = B(); s.do_work()`

## WHY THIS IS INTENTIONALLY PINNED WRONG

v0 uses `ast.walk` (BFS) to scan function bodies. Both branches of the if/else
are visited, and `var_types["s"]` is overwritten by each Assign in BFS order.
`If.body` (s=A) is visited before `If.orelse` (s=B), so B wins.

`s.do_work()` resolves to `B.do_work` — correct for the else-branch, wrong overall.

## Regression target

This fixture pins the wrong-but-deterministic behavior so that a future
flow-sensitive pass can use it as a regression target. The expected.json
asserts the WRONG B.do_work edge. A reviewer who sees this test and thinks
"the test is wrong" is right — intentionally. Do not fix the test without
implementing flow-sensitive analysis.

## Correct behavior (future)
A flow-sensitive pass should emit edges to BOTH A.do_work and B.do_work
(conservative: all reachable paths), or model the join point properly.
