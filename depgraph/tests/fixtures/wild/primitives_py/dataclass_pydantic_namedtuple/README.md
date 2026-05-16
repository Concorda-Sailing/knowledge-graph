# Fixture: dataclass_pydantic_namedtuple

## What it tests

Three class-decoration styles that all produce annotated field declarations,
coexisting in a single file with overlapping field names (`x`, `y`, `label`):

1. `@dataclass class PointDC` — standard dataclass with `field(default_factory=…)`.
2. `@dataclass class PointDC3D(PointDC)` — dataclass subclassing another dataclass.
3. `class PointNT(NamedTuple)` — NamedTuple using annotated-assignment syntax.
4. `class PointPydantic` — simulated Pydantic model with a nested `Config` inner class.

## Why it's tricky

1. **Overlapping field names.** `x` and `y` appear in `PointDC`, `PointNT`, and
   `PointPydantic`. The extractor must scope each to its owning class, producing
   distinct ids like `PointDC.x` vs `PointNT.x` vs `PointPydantic.x`.
2. **Nested Config class.** `PointPydantic.Config` is a genuine nested `ClassDef`.
   The extractor recurses into it, emitting `PointPydantic.Config` (class) and
   `PointPydantic.Config.frozen` (variable). This exercises the same recursion
   path as `nested_everything` but within a model-style class.
3. **Decorator capture.** `@dataclass` is captured in the class primitive's
   `signature.decorators` list. NamedTuple and the simulated Pydantic class have
   no decorator — their decorators list is empty.
4. **`field(default_factory=list)`** — the `tags` field is still an `AnnAssign`
   node even with a complex initializer; the extractor emits it as a variable
   with `value_text = "field(default_factory=list)"`.
