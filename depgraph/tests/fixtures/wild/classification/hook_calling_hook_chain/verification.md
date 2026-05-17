## Prediction (written before running classifier)

Chain: `useFoo` → `useBar` → `useState` (external::npm::react::useState).

The plan states "all 3 classify as hook." The hook classifier rule is:
`use<Capital>` function that calls a known external React hook.

- `useBar` calls `useState` (external) directly → hook. Predicted: hook.
- `useFoo` calls `useBar` (a local user-defined function, not an external
  hook target) → the classifier only checks calls against
  `known_hook_externals = {external::npm::react::<name>}`. `useBar`'s id is
  `r::src/useBar.ts::useBar`, not in that set. Predicted: NOT hook.

Overall prediction: `useBar = hook`, `useFoo = None`.

## Actual result (after running)

`useBar = hook`, `useFoo = None`. Matches prediction.

## v0 limitation documented

The hook classifier does a single-pass, direct-call check only. It does not
propagate classification transitively through user-defined hook chains. The
comment in `hook.py` line 29-30 acknowledges this:

> Transitive: calls another user-defined hook — handled by a future
> second-pass in Task 5.7 once all hooks are classified.

To get `useFoo` to classify as hook in the current implementation, it must
directly call a known external React hook (e.g. `useState`), not just call
another user-defined hook.

This fixture pins the v0 one-hop behaviour. When transitive propagation is
implemented (Task 5.7 second-pass), update `expected.json` to include
`{"id": "r::src/useFoo.ts::useFoo", "kind": "hook"}` and re-verify.
