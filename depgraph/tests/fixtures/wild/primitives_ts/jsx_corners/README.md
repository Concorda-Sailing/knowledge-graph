# jsx_corners

## What's tested

Four JSX-adjacent patterns that challenge naive `returns_jsx` detection:

1. **`React.memo` wrapper** — the component function is wrapped in `memo(fn)`. The inner function
   returns JSX, but a naive extractor checking the top-level variable's initializer may see the
   `memo(...)` call expression, not the inner arrow function body.

2. **Array of JSX elements** — a function returns `[<A/>, <B/>]`. The return type is an array,
   not a single JSX element, but JSX nodes exist in the body. `bodyHasJsx` must detect them.

3. **Conditional null return** — `if (x) return null; return <div/>`. One branch returns null,
   the other returns JSX. The function still classifies as `returns_jsx=true` because JSX exists
   anywhere in the body.

4. **JSX created but not returned** — a function builds a JSX element and stores it in a variable
   but returns `void`. This function should still have `returns_jsx=true` if the extractor uses
   `bodyHasJsx` (which checks for any JSX descendant), or `returns_jsx=false` if it only checks
   return expressions. The current extractor uses `bodyHasJsx` (descendant scan), so this will
   be `returns_jsx=true`. This fixture pins that behavior.
