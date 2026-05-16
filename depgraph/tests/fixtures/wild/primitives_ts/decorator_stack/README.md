# decorator_stack

## What's tested

Class methods with 3+ stacked decorators, including parameterized decorators (decorator factories
that are called with arguments, e.g. `@Role("admin")`).

## Why a naive extractor would break

A naive extractor may only capture the first decorator, or may call `d.getName()` on a
parameterized decorator where `getName()` returns the call expression rather than the callee name,
producing strings like `"Role("admin")"` instead of `"Role"`.

The extractor must use `d.getName()` (which ts-morph resolves to the identifier name even for
call-expression decorators) and collect ALL decorators in order. The `signature.decorators` array
should contain dotted/simple names only, not argument lists.
