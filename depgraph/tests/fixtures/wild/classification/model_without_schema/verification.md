## Prediction (written before running classifier)

Class: `User` in `models/user.py`. Has:
- `extends` edge to `external::pypi::sqlalchemy::Base` (ORM base ✓).
- `references` edge to `r::migrations::users` via `__tablename__`.

The model classifier collects `schema_ids` as the set of primitive ids where
`p.get("kind") == "schema"`. The corpus contains only the `User` class — no
primitive with id `r::migrations::users` and `kind = "schema"` is present.

Therefore `r::migrations::users` is NOT in `schema_ids`. The references edge
condition `e["target"] in schema_ids` fails. `schema_ref` stays None.

Both conditions must hold (`extends_orm and schema_ref is not None`). Since
`schema_ref` is None, no model decision is emitted.

Prediction: `kind = None`.

## Actual result (after running)

`kind = None`. Matches prediction.

## Design property confirmed

The model classifier validates the full triangle: ORM base extension AND an
in-corpus schema primitive linked via `__tablename__`. A dangling (unresolved)
references edge — where the target id simply does not exist in the corpus —
does not satisfy the schema condition. This is correct: if the schema migration
table has not been extracted into the corpus, the model-schema link cannot be
verified, so the class stays unclassified rather than being misclassified.

This is distinct from `orphan_model` (no references edge at all). Here the
references edge exists but points at a missing target. Both correctly yield
`kind = None`.
