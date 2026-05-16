# name_collisions

## What's tested

A single file where the string `"value"` appears simultaneously as:
- a class field (property) named `value`
- a static method named `value` (disambiguated by `:static` suffix in the id)
- an instance method named `getValue` (different string to avoid field/method id collision)
- a type alias named `value` at module scope

## Why a naive extractor would break

Without the `:static` suffix, the static method `Container.value` and the instance field
`Container.value` would produce the same id, silently colliding. A naive extractor that
emits `ClassName.memberName` for all members loses the static method or the field.

The extractor resolves this via:
- Class field `value` → id `Container.value` (primitive=variable, owner=class)
- Static method `value` → id `Container.value:static` (primitive=function, owner=class, `:static` suffix)
- Instance method `getValue` → id `Container.getValue` (different name avoids collision with field)
- Type alias `value` → id `value` (primitive=class, owner=null, module scope — no collision)

Note: if an instance method and a class field share the exact same name, the extractor
produces identical ids for both (known limitation — no kind suffix on instance methods).
This fixture avoids that collision by using a distinct instance method name.
