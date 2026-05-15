# Evaluation harness

## Cases

Each case is a directory:

```
corpus/<lang>/<name>/
├── source/         input tree (small, real-ish code)
├── expected.json   declared ground truth: { "nodes": { "<kind>": ["<id>", ...] } }
├── case.toml       language + detectors to enable
├── README.md       what this case tests
└── judgments/      Claude-Code-session judgment files accumulate here
```

Only declared expectations are checked. Omitted fields = "don't care."

## Modes

```bash
# Deterministic (gates PRs):
python3 -m extractors.eval.harness run python --case _seed_imports
python3 -m extractors.eval.harness run python   # all python cases

# Judgment (advisory, hand-reviewed in a Claude Code session):
python3 -m extractors.eval.harness judge python --case _seed_fastapi
# Read corpus/python/_seed_fastapi/judgments/pending.md and save your
# judgment to corpus/python/_seed_fastapi/judgments/<YYYY-MM-DD>.md
```

## Authoring a new case

1. `mkdir corpus/<lang>/<name>` and populate `source/`, `expected.json`, `case.toml`, `README.md`.
2. Run `harness.py run <lang> --case <name>` and iterate until it passes (or until the gap is intentional and documented).
3. Commit. The case becomes part of CI from then on.
