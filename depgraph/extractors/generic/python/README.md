# Python language extractor

Walks Python source with stdlib `ast`. Emits module/class/function
primitives plus import/call edges. Detectors layer on framework
semantics (FastAPI endpoints, SQLAlchemy models, etc.).

## Run

```bash
python3 extract.py \
  --repo-key api --repo-path ~/myproj-api \
  --data-dir ~/myproj-knowledge-graph/depgraph \
  --detectors fastapi,sqlalchemy,pydantic,pytest
```

## Authoring a detector

1. Copy `TEMPLATE_detector.py` to `detectors/<name>.py`.
2. Implement `detect()` — see the template for the contract.
3. Add a single-file test in `~/tools/knowledge-graph/depgraph/tests/extractors/test_python_detectors.py`.
4. Add an eval case under `eval/corpus/python/_seed_<name>/`.
5. Open a PR. See `CONTRIBUTING-detectors.md` at repo root.

## Detector lookup order

1. Framework dir: `~/tools/knowledge-graph/depgraph/extractors/generic/python/detectors/`.
2. Project-local: `<data-repo>/depgraph/extractors/detectors/` (via `--detector-path`).
