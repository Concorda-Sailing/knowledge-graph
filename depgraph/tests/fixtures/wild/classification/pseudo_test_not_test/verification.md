## Prediction (written before running classifier)

Function: `test_calculate` in `lib/calculations.py`.

The test classifier fires iff any of:
(a) has a `tests` edge outgoing — No, corpus has no tests edge.
(b) has a `pytest.` decorator — No, no decorators.
(c) lives in a test-named file AND name starts with "test".

Condition (c): the file path is `lib/calculations.py`. The test-file check
in `test_kind.py` uses `_in_test_file`:
- `filename.startswith("test_")` → "calculations.py" does not start with "test_".
- `filename.endswith("_test.py")` → no.
- `".test." in filename` → no.

`lib/calculations.py` is NOT a test file. Condition (c) fails even though the
function name starts with "test".

Prediction: `kind = None`.

## Actual result (after running)

`kind = None`. Matches prediction.

## Key design property confirmed

The test classifier requires BOTH a test-file path AND a test-prefixed name
(condition c). Name alone is not sufficient. This is correct: library code
often has functions named `test_*` for internal testing helpers, benchmarks,
or validation routines that are not pytest test functions.

The path-gate is the essential discriminator. A function named `test_calculate`
in `tests/test_calculations.py` WOULD classify as test. In `lib/calculations.py`
it must not — and does not.
