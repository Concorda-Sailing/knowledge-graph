# Verification log: dunder_zoo

**Last reviewed:** 2026-05-16 by Claude (sonnet subagent)
**Status:** ✓ verified

## Pre-read prediction
*Written before looking at expected.json.*

The file defines one class `DescriptorMixin` with:
- `__slots__` list assignment → variable primitive `DescriptorMixin.__slots__`
- `__init_subclass__` method → function primitive
- `__set_name__` method → function primitive
- `__class_getitem__` method → function primitive
- `@property def value` → function primitive `DescriptorMixin.value` (decorators: ["property"])
- `@value.setter def value` → function primitive with *same id* `DescriptorMixin.value` (decorators: ["value.setter"])

Plus the module primitive `src/dunders.py`.

Expected ids (7 unique, noting the setter/getter collision):
1. `fixture::src/dunders.py` (module)
2. `fixture::src/dunders.py::DescriptorMixin` (class)
3. `fixture::src/dunders.py::DescriptorMixin.__slots__` (variable)
4. `fixture::src/dunders.py::DescriptorMixin.__init_subclass__` (function)
5. `fixture::src/dunders.py::DescriptorMixin.__set_name__` (function)
6. `fixture::src/dunders.py::DescriptorMixin.__class_getitem__` (function)
7. `fixture::src/dunders.py::DescriptorMixin.value` (function — getter and setter collapse to one id in a set)

No packages (no `__init__.py`). No edges in Phase 2.

## Prediction vs expected.json
- Matches: all 7 ids predicted correctly before writing expected.json.
- The property collision was anticipated; expected.json lists only one `value` entry (set semantics in the test).

## Expected vs actual (from running the extractor)
Ran:
```
extract_repo(repo_key='fixture', repo_path=<dunder_zoo>)
```
Actual output: 8 primitives emitted (getter + setter both appear as separate dicts),
but both carry id `fixture::src/dunders.py::DescriptorMixin.value`. As a set: 7 unique ids.
All 7 expected ids present. No extra ids.

- Matches: ✓ all 7

## Notes
**Pinned-wrong behavior:** property getter and setter emit identical ids. The test
harness compares sets so the collision is invisible to the test — both passes succeed.
Any downstream consumer that builds a dict keyed by id will silently drop the getter,
retaining only the setter (Python dict last-write-wins). A future fix should either:
(a) append `#getter` / `#setter` fragments to the id, or (b) merge getter+setter into
one primitive with a `has_setter: true` attribute. This is a v0 limitation; do not fix
in extract.py during this task.
