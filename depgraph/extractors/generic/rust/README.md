# Rust language extractor

Walks Rust source via `py-tree-sitter` + `tree-sitter-rust`. Emits
module/class (struct/enum/trait)/function primitives plus use-declaration
imports and call edges. No framework detectors shipped at launch — see
`CONTRIBUTING-detectors.md` to add one.

## Run

```bash
python3 extract.py --repo-key svc --repo-path ~/myproj-svc \
  --data-dir ~/myproj-knowledge-graph/depgraph --detectors ""
```
