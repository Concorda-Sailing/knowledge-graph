## Prediction (written before running extractor)

### Pattern
Module-scope: `COUNTER = 0`, `NAME = "default"`.
Functions: `get_counter` reads COUNTER, `get_name` reads NAME, `increment` assigns COUNTER,
`reset` assigns COUNTER and NAME.

### `_attach_var_access_edges` logic

`local_vars = {"COUNTER": fixture::src.py::COUNTER, "NAME": fixture::src.py::NAME}`

For each function, `ast.walk(fn_node)` visits all Name nodes.

#### `get_counter`: `return COUNTER`
- `Name("COUNTER", Load)` → reads edge to COUNTER

#### `get_name`: `return NAME`
- `Name("NAME", Load)` → reads edge to NAME

#### `increment`: `global COUNTER; COUNTER += 1`
- `COUNTER += 1` compiles as `ast.AugAssign(target=Name("COUNTER", Store), ...)`
- `ast.walk` visits `Name("COUNTER", Store)` → assigns edge to COUNTER
- Also visits `Name("COUNTER", Load)` (the load side of +=) → reads edge to COUNTER
- So `increment` gets BOTH reads AND assigns edges for COUNTER

#### `reset`: `COUNTER = 0; NAME = "default"`
- `Name("COUNTER", Store)` → assigns
- `Name("NAME", Store)` → assigns
- No reads (pure store)

### Predicted edges from each function:
- `get_counter`: reads COUNTER
- `get_name`: reads NAME
- `increment`: reads COUNTER AND assigns COUNTER (from AugAssign: both Load and Store)
- `reset`: assigns COUNTER, assigns NAME

### Note on `global` statements
`global COUNTER` is `ast.Global` node — not a Name node, not emitted as an edge.

### Post-run correction
Prediction was wrong on `increment`. `COUNTER += 1` is `ast.AugAssign(target=Name(Store), ...)`.
The target Name has `Store` ctx — that's one assigns edge. There is NO separate `Load` Name node
for the left-hand side in an AugAssign. Python's AST doesn't represent the implicit read as a
Name(Load) node. So `increment` gets only assigns, not reads. Prediction corrected.
