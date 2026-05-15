# Go language extractor

Walks Go source via `py-tree-sitter` + `tree-sitter-go`. Emits
module/class (struct/interface)/function primitives plus import/call
edges. No framework detectors shipped at launch — see
`CONTRIBUTING-detectors.md` to add one.

## Run

```bash
python3 extract.py --repo-key svc --repo-path ~/myproj-svc \
  --data-dir ~/myproj-knowledge-graph/depgraph --detectors ""
```
