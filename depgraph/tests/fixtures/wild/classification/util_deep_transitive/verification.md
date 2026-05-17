## Prediction (written before running classifier)

Chain: `list_events` (endpoint) → `fetch_events` → `query_events` →
`get_cached` → `serialize`.

The util classifier does forward BFS from the classified set. After endpoint
classification, `list_events` is classified. BFS expands:

Round 1: from `list_events` → reaches `fetch_events` (calls edge). Not yet
classified → util, added to frontier.
Round 2: from `fetch_events` → reaches `query_events`. Not classified → util,
added to frontier.
Round 3: from `query_events` → reaches `get_cached`. Not classified → util,
added to frontier.
Round 4: from `get_cached` → reaches `serialize`. Not classified → util, added
to frontier.
Round 5: `serialize` has no calls edges → frontier empty, BFS terminates.

Util classifier also expands through newly-classified util nodes (the frontier
check uses `reachable` not just `classified_ids`). All four interior functions
are in the same BFS wave regardless of discovery order.

Prediction: `list_events = endpoint`, all four inner functions = `util`.

## Actual result (after running)

`list_events = endpoint`, `fetch_events = util`, `query_events = util`,
`get_cached = util`, `serialize = util`. Matches prediction exactly.

## BFS single-pass confirmed

The util classifier's frontier expands through newly-reached util nodes
immediately (they are added to `frontier` when discovered). A node classified
as util in round N can expand in round N+1. This means the full depth-4 chain
is resolved in a single pass of the classifier. No second invocation needed.

This is important: service also uses BFS (from endpoints), but it seeds only
from endpoints and expands through `calls`. Both classifiers converge in one
pass because they use expanding frontiers, not fixed-point iteration.
