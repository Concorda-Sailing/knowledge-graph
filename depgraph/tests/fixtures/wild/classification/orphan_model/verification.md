## Prediction (written before running classifier)

Class: `Event` in `models/event.py`. Has an `extends` edge to
`external::pypi::sqlalchemy::Base`. No `references` edge to any schema
primitive (no `__tablename__` assignment in source).

The model classifier requires BOTH:
1. `extends` edge to a known ORM base class (last segment "Base" → matches).
2. `references` edge to a primitive with `kind == "schema"` via a
   `orm_schema_link_via` (default: `"__tablename__"`).

Condition 1 is met. Condition 2 is not met — no references edge exists.

Prediction: `kind = None`. Both conditions must hold; one is not enough.

## Actual result (after running)

`kind = None`. Matches prediction.

## Framework behaviour note

The comment in `model.py` line 56 documents this explicitly:

> extends_orm without schema_ref: orphan mapper — kind stays None.
> Graphui can surface these as "classes extending ORM base but unclassified".

No warning is emitted by the classifier at runtime. The framework does not
log a warning for orphan mappers; it simply leaves the kind unset. A future
graphui query (`classes extending ORM base, kind=None`) can surface these for
developer attention. The classifier's job is classification, not diagnostics.
