# Fixture: dunder_zoo

## What it tests

Python's descriptor-protocol dunders (`__init_subclass__`, `__set_name__`,
`__class_getitem__`) and a `__slots__` list declaration, plus a
`@property` / `@<name>.setter` pair.

## Why it's tricky

1. **`__slots__`** is an `Assign` node whose target is `__slots__` — the
   extractor sees it as a plain variable. Correct behavior: emit as
   `variable` with `name = "DescriptorMixin.__slots__"`.
2. **Dunder methods** look like ordinary `FunctionDef` nodes. The extractor
   must not special-case them; they emit as `function` primitives.
3. **Property getter + setter** both use the same Python name (`value`).
   The extractor emits *two* primitives with identical ids
   (`DescriptorMixin.value`). Because the test harness compares *sets* of
   ids, the collision collapses to one entry — both passes succeed. This
   is a v0 pinned-wrong behavior: the setter silently shadows the getter in
   any downstream consumer that indexes by id. Documented but not fixed here.
