# basic_python — Option C test-coverage walker

Pin fixture for issue #52 / Option C. Exercises the simplest end-to-end
shape: a production module + a test file that imports it, where the
production extractor was told to exclude the test file but the
coverage walker still maps it back to the production symbol.

## Layout

- `src/widget.py` — production module with two top-level symbols
  (`make_widget` function, `WIDGET_DEFAULT` variable).
- `src/helpers.py` — second production module so we can verify the
  index discriminates between covered and uncovered nodes.
- `src/tests/test_widget.py` — test file that imports `make_widget`
  and `WIDGET_DEFAULT` from `widget.py`; the helpers module is NOT
  imported.

## Expected coverage

After production extraction (with `exclude_paths = ["**/tests/**"]`)
followed by the test-coverage walker (with default `test_paths`):

- `fixture::src/widget.py::make_widget` → covered by `test_widget.py`
- `fixture::src/widget.py::WIDGET_DEFAULT` → covered by `test_widget.py`
- `fixture::src/widget.py` → covered by `test_widget.py` (module-level)
- `fixture::src/helpers.py::format_label` → NOT covered (no test)

The fixture also asserts that the production primitive set does NOT
include any test-file primitives (the walker must not pollute the
production graph).
