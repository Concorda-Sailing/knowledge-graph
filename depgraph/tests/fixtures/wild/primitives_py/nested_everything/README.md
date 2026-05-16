# Fixture: nested_everything

## What it tests

Two axes of nesting:

1. **Class-in-class** (`Outer.Inner.Deepest`) — the extractor recurses through
   `ClassDef` nodes inside class bodies, building dotted qualnames and setting
   `owner` to the enclosing class id at each level.
2. **Class/function inside a function** — `LocalClass` inside `Outer.outer_method`,
   `FuncLocal` and `nested_def` inside `top_func` — the extractor does NOT recurse
   into `FunctionDef` bodies, so these are invisible.

## Why it's tricky

The recursion boundary is defined by node type, not by depth. `_emit_class` recurses
on `ClassDef` children of a class body, but `_walk_module_body` and `_emit_class`
both skip the body of `FunctionDef` / `AsyncFunctionDef` nodes. A naive
implementation that walks the entire AST (e.g. `ast.walk`) would incorrectly extract
function-local classes as module primitives.

## v0 documented limitation

Classes and functions defined inside a function body are not extracted. This is
intentional: function-scope names are not part of the module's public surface and have
no stable identity across call sites. A future flow-sensitive pass could opt in to
tracking closures, but that is explicitly out of scope for Phase 2.
