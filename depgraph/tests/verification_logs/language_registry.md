# Verification log: language registry

**Last reviewed:** 2026-05-16 by Claude (haiku subagent under Opus controller)
**Components:** load_languages, Language
**Source:** depgraph/lib/language_registry.py

## Inputs exercised

For each input below, the "Predicted" column was filled in BEFORE running.
Discrepancies between Predicted and Observed (if any) are noted at the bottom.

| Input | Predicted | Observed |
|---|---|---|
| `load_languages(framework_toml)` — framework-only, no project.toml | 3 languages: typescript, python, sql | 3 languages: typescript, python, sql |
| Names of framework-only languages | `{"typescript", "python", "sql"}` | `['typescript', 'python', 'sql']` (insertion order preserved in Python 3.7+ dict) |
| `typescript` extensions | `[".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"]` | `['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs']` |
| `python` runtime | `"python"` | `'python'` |
| `sql` extractor path | resolved absolute path ending in `depgraph/extractors/sql/extract.py` | `/home/lgreenlee/tools/knowledge-graph/depgraph/extractors/sql/extract.py` |
| `load_languages(framework_toml, project_toml)` where project adds `[languages.yaml]` | 4 languages; yaml in the set; yaml extractor resolves relative to project_toml parent | 4 languages: `['typescript', 'python', 'sql', 'yaml']`; yaml extractor `/tmp/tools/extract_yaml.py` |
| `load_languages(framework_toml, project_toml)` where project overrides `[languages.python]` with different extensions `[".py", ".pyw"]` | 3 languages; python extensions updated; other languages unchanged | 3 languages; python extensions `['.py', '.pyw']`; extractor `/tmp/myextractors/python_custom.py` |
| `load_languages(framework_toml, Path("/tmp/does_not_exist.toml"))` — nonexistent project.toml | Falls back to framework-only (3 languages) — predicted the `project_toml.exists()` guard handles this | 3 languages: `['typescript', 'python', 'sql']` |

## Observations

**Finding 1 — Extractor paths resolve relative to different roots for framework vs project:**
Framework extractor paths resolve relative to `framework_toml.parent.parent` (the repo root, one
level above `depgraph/`). Project extractor paths resolve relative to `project_toml.parent`. This
asymmetry is intentional and documented in the docstring, but means a project.toml that tries to
reference a framework extractor with a `depgraph/extractors/...` path will resolve to a different
absolute location than the framework entry would — potentially a nonexistent path. Worth verifying
at load time (e.g., assert extractor path exists) rather than failing silently at extraction time.

**Finding 2 — Language insertion order is preserved:**
`merged` is a plain `dict`, so iteration order is insertion order (Python 3.7+). Framework
languages come first in the order they appear in `languages.toml`; project additions are appended
at the end. Project overrides of existing names replace the value in place but do NOT move the key
to the end — the name stays at its original position. This means `list(merged.values())` returns
framework languages first, then any project-only additions, with overridden framework entries
remaining at their original position. Confirmed by the override test: python stayed second even
after override.

**Finding 3 — No validation that extractor path exists:**
`load_languages` calls `.resolve()` on the extractor path but does not assert the file exists.
A typo in `project.toml`'s extractor field produces a `Language` object with a non-existent
resolved path, with no error at load time. The error surfaces only when the extractor is actually
invoked. Adding a `Path.exists()` check in `_read_languages_section` would make misconfiguration
fail fast.

**Finding 4 — `Language` is a frozen dataclass with `extensions: list[str]`:**
`frozen=True` prevents re-assigning fields, but `extensions` is a mutable list. A caller who
obtains a `Language` and does `lang.extensions.append(".pyi")` mutates the list in place without
triggering a `FrozenInstanceError`. This is a standard Python gotcha with frozen dataclasses
containing mutable fields. Low risk in current usage (languages are loaded once and read-only by
convention) but worth flagging if Language objects are ever cached or shared across threads.

## Status
✓ verified — all predictions matched observed output. Four structural observations recorded above, none blocking.
