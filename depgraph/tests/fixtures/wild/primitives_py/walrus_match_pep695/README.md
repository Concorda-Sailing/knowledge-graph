# Fixture: walrus_match_pep695

## What it tests

Three modern Python syntax features that a naive AST walker might choke on:

1. **Walrus operator** (`if _version_match := re.match(…)`) at module scope — the
   `NamedExpr` is inside an `If` test, which is an `If` node in `tree.body`. The
   extractor only handles `Assign`, `AnnAssign`, `ClassDef`, and `FunctionDef` at
   the body level, so the walrus binding is not extracted. `VERSION_MAJOR` and
   `VERSION_MINOR` are `AnnAssign` nodes inside the `If` body (not `tree.body`
   direct children) — also not extracted.

2. **`match`/`case`** (`match value: case …`) — Python 3.10+ `Match` statement.
   The extractor does not handle `Match` nodes (they are not `Assign`/`AnnAssign`/
   `ClassDef`/`FunctionDef`), so the match block is transparent. The function
   containing it (`classify_input`) is extracted normally.

3. **PEP 695 generics** — `class Stack[T]` and `def first[T](…)` use type parameter
   syntax available in Python 3.12+. The extractor reads `node.type_params` (a list
   of `TypeVar` nodes) and stores their names in `attributes.template_parameters`.
   The class and function primitives are emitted normally; the type parameter syntax
   does not change their ids or primitive type.

## Why it's tricky

- Walrus bindings look like assignments but are syntactically `NamedExpr` inside
  other expressions, not top-level `Assign` nodes. An `ast.walk`-based extractor
  would incorrectly pick them up.
- `Match` is a statement kind added in Python 3.10; older AST visitors error or
  silently skip it. The extractor's explicit dispatch (`isinstance` checks for known
  node types) naturally skips `Match` without error.
- PEP 695 `type_params` is a Python 3.12 addition; `getattr(node, "type_params", [])`
  in the extractor gracefully degrades on older Python versions.
