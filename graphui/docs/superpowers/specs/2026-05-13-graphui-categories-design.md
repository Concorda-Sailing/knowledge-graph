# graphui — categories & navigation overhaul

Date: 2026-05-13
Status: design approved, awaiting plan

## The problem

The current graphui surfaces categories of knowledge as two flat card grids on the dashboard (depgraph kinds + source repos) and a flat table at `/graph/knowledge`. Several real categories the substrate already produces have **no UI at all**:

- Telemetry (`telemetry/injections.jsonl`, `telemetry/acknowledgments.jsonl`) — which rules actually fire on edits, which dossiers Claude reads.
- Calibration (`logigraph/calibration/runs/`) — rule-injection accuracy over time.
- Activity history beyond a single node — there is no week/month timeline.

Several categories that exist as pages are reachable only by drilling three levels deep:

- Domain rollups (`/graph/domain/X/rollup`).
- Per-repo inbound / outbound / external dependency counts (not surfaced anywhere).
- Dead-code candidates (zero inbound refs, no recent activity) — not surfaced anywhere.

There is no search — keyword, prefix, or semantic — at all.

The user's lived experience: "Nodes aren't well rolled up. There are different views for things. I need a logical progression and a search to find specific things."

## Direction

**Repo-first dashboard with cross-cuts above and graph-health beside.** Repos are the spine because the user expects up to ~50 of them, most dormant, and a primary goal is hunting dead repos / dead code. Cross-cutting knowledge (rules / domain / processes) sits above the repo list because it frames the project conceptually but is a small, stable set. Graph-health (telemetry + calibration + activity) gets dashboard real estate because the system's own observability has been invisible.

All list views collapse to a single universal node-list component. All detail pages share the same chrome (header → stat row → tabbed main pane).

## Dashboard layout

Top to bottom:

1. **Top bar** — `◆ graphui` brand · global search input (semantic + keyword + id-prefix modes) · Issues badge · Review badge.
2. **Activity strip** — three columns:
   - Today (`+12 nodes · 3 drafts · 2 drift · 1 rule authored`).
   - 7-day daily-add sparkline.
   - 30-day rollup summary.
   - `activity timeline →` link to `/graph/activity`.
3. **Graph health tile** — three sub-tiles:
   - *Telemetry · injections (30d)*: total fires, trend vs prior 30d, ack rate, dead-rule count, never-acknowledged dossier count.
   - *Calibration · last run*: accuracy %, regressions, named drifted rules; link to run history.
   - *Hottest rules (30d)*: top-3 by fire count; `see all telemetry →` link to `/graph/telemetry`.
4. **Cross-cutting knowledge** — three cards: Rules, Domain, Processes. Each shows count, secondary projection (rules→repos, domain→referenced-by, processes→spans-repos), and a namespace/subkind preview line. Domain and Processes have `rollup ↗` affordances.
5. **Tracked repos** — header with sort dropdown (`activity ↓` default; alternatives: alpha, inbound deps, dead-code score) and filter chips (`active · 12` | `dormant · 29` | `dead candidates · 6` | `all · 47`).
   - Active repos render as full cards (see below). Dormant collapse into a single expandable row. Dead candidates render as a compact callout table with eviction-plan affordance.

### Repo card (full, active)

```
concorda-web                            TypeScript · React · Next       +5 today
activity (7d): ▁▃▅▇█▆▇   47 commits · 134 nodes · 87% current
[ state bar ]
[component · 87] [hook · 34] [page · 13]
[📁 app/] [📁 components/] [📁 lib/] [📁 hooks/]
─────────────────────────────────────────────────────────────
↑ inbound 7 repos   ↓ outbound 3 repos   ⊕ external 142 pkgs
🧷 6 rules   ⤳ 4 processes              ⚠ 2 stale claims
```

### Dormant + dead-candidate sections

Dormant: collapsed banner showing aggregate counts (`29 dormant repos · 312 nodes · 47 stale claims`); expanding reveals compact rows (one line per repo: name · last-commit-age · nodes · ↑inbound · ↓outbound).

Dead candidates: distinct visual (amber border), table with columns repo · last · nodes · inbound · outbound · rules. Row click opens the standard repo detail page (the dedicated eviction-plan workflow is its own spec — see Out of Scope).

## Repo detail page

URL: `/graph/repo/{basename}` (existing path).

Layout:

- **Breadcrumb + in-repo search** (`🔍 search in concorda-web …`).
- **Header**: name · language stack · today delta · 7-day sparkline · last-push timestamp.
- **Stat row** (chips): `134 nodes` · `87% current` · `↑ 7 inbound` · `↓ 3 outbound` · `⊕ 142 ext pkgs` · `⚠ 12 dead-code candidates` · `🧷 6 rules · 4 processes`.
- **Two-column body**:
  - Left rail (30% width):
    - *Areas* — collapsible directory tree with node counts per dir.
    - *Kinds* — count list + Tier (A/B/C) breakdown.
    - *Cross-cuts* — named lists: 6 rules, 4 processes, 11 domain entities, each item linking to its detail page.
  - Main pane (tabbed):
    - **Nodes** (default) — universal sortable/filterable node list. Filter chips: kind · area · tier · state. Sort: fan-in (default) · title · last-edit · state.
    - **Dependencies** — three sub-sections (inbound, outbound, external pkgs). Inbound/outbound show per-symbol detail (which symbol in which other repo references which symbol in this repo).
    - **Dead code** — nodes in this repo with zero inbound refs. Sortable by last-edit / fan-out / external pkgs touched.
    - **Telemetry** — rule fires that occurred on edits to files in this repo, scoped per-rule and per-file.
    - **Activity** — chronology of node adds/edits/drafts/reviews/drift events for this repo.

## Semantic search

Single search input in the top bar; results render in a full-page overlay.

- **Modes**: `semantic` (default for queries ≥ 3 tokens) · `keyword` (BM25 on titles, IDs, dossier headings) · `id prefix` (exact prefix on node IDs). User can pin a mode; otherwise auto-selected by query shape.
- **Scope chips**: rules · domain · processes · code · dossiers. Default all-on; user can narrow.
- **Hybrid retrieval**: BM25 on titles + cosine similarity on embedded dossier/statement/summary/step prose, blended with default weights `0.4 * BM25 + 0.6 * cosine` (tunable per query via a `weights=` param; the chosen defaults err toward semantic since the explicit reason the user is adding this is "find rules I can't keyword-recall").
- **Match-reason snippet**: every hit returns the highest-similarity span; UI renders it as a quoted italic line under the title with matched phrases highlighted.
- **Result row**: kind badge · node id · match score · state · matched-span snippet · claim list (for rules) or area (for code).
- **Keyboard**: `⌘K` focus search · `↑/↓` navigate · `↵` open · `esc` close.

### Embedding pipeline

- Triggered by `bin/depgraph regen` and `bin/logigraph regen` (extend reconcile).
- Embeds: every dossier body, every rule `statement`, every domain `summary`, every process step `description`. One vector per logical chunk; chunks > 512 tokens get window-split with 128-token overlap.
- Embedding endpoint: the felix Gemma 4 26B OpenAI-compatible endpoint already in user memory (`reference_gemma_llm`).
- Storage: per-data-dir `_index/embeddings.bin` (one row per chunk, fp16, plus a sidecar `_index/embeddings.jsonl` mapping row → node-id + chunk-span). Regenerated incrementally; rows for unchanged dossiers carry forward by content hash.
- Server-side retrieval in the FastAPI app: load both files into memory on app start; cosine search is brute-force at this corpus size (< 10k chunks). Re-load on file mtime change.

## New pages

| Path | Purpose |
|---|---|
| `/graph/activity` | Full chronology, filterable by event type (node added · draft authored · reviewed · drift · rule fired in calibration) and date range. |
| `/graph/telemetry` | Per-rule + per-dossier injection counts, ack rates, never-fired list, hottest / coldest rules. Tab on each rule/node detail. |
| `/graph/calibration` | Run history, per-prompt accuracy, regressions, drift trajectory per rule. Tab on rule detail shows that rule's calibration history. |
| `/graph/search` | Server-rendered results page, served when the user submits the top-bar form; the typeahead/overlay variant calls the same backend via `/graph/api/search.json`. |

## New data the loader must compute

Per-repo, per-regen:

- 7-day and 30-day commit count (from `git log --since`).
- 7-day daily-bucket commit array for sparkline.
- Today's node-add count (compare current node set to one regen ago, or to a stamp file).
- Activity state classification: `active` (commit in last 7d) · `dormant` (no commit in 30d) · `dead-candidate` (no commit in 180d AND zero inbound from other tracked repos).
- Language detection: file-extension histogram → primary 1–2 languages, plus framework hints from `package.json` / `pyproject.toml` / etc.
- Top-level area list (immediate child dirs containing tracked nodes) with per-area node counts.
- Inbound dep count: # of *other* tracked repos that contain a node whose dependents pointer crosses into this repo.
- Outbound dep count: symmetric.
- External package count: from `package.json` `dependencies` + `requirements.txt` / `pyproject.toml`. Counted per repo, not deduped across the graph.

Per-rule:

- 30-day injection count (from `injections.jsonl`).
- 30-day acknowledgment count (from `acknowledgments.jsonl`).
- "Never fired" flag (≥ 30 days since regen with zero injections).
- Latest calibration accuracy + delta vs previous run.

Per-dossier:

- "Never acknowledged" flag.

## Out of scope for this design

- A full graph-topology visualization (force-directed node-edge view). Useful eventually but a separate spec — the substrate work here is the prerequisite.
- Framework self-tracking project switcher in the UI (the dogfood data dir works via env var today; first-class UI later).
- Eviction-plan generation for dead-code candidates — the list is surfaced; the "now what" workflow is its own spec.
- Authoring affordances (rule editor, dossier editor) — graphui remains a viewer; authoring stays CLI + filesystem.

## Decisions made (call-outs for review)

- **"Contribution rate" = 7-day commit count.** The user's phrase from the brainstorm; default sort field on the repo list. Alternative interpretations (new-nodes-per-day, edit churn) become secondary sort options.
- **Cross-cutting strip lives above repos, not below.** The user explicitly asked for this on v2 reaction.
- **Single search input, modes auto-detected.** Pinning is available but the default UX is one box, no toggles to learn.
- **Embeddings via felix Gemma, not OpenAI.** Local, free, already in the substrate.
- **Repo card footer surfaces rule + process counts.** Cross-cuts are projected onto each repo, not only summarized in the strip — so "what governs this repo" is one click away.
- **Universal node-list component reused everywhere.** Dashboard drill-in, repo detail Nodes tab, search results, knowledge page, kind detail — all the same component with different default filters.

## Implementation notes

The implementation plan will need to sequence:

1. Loader extensions (the "new data" section above) — strictly additive, no UI changes yet.
2. Dashboard rewrite (`index.html` + main.py `index()` route) consuming the new loader data.
3. Repo detail rewrite (`repo.html` + the route) — left rail + tabs.
4. Universal node-list extraction into a partial template.
5. Search backend: embedding pipeline in `reconcile.py`, retrieval endpoint in `main.py`, results template.
6. Telemetry page (read-only over the jsonl files).
7. Calibration page (read-only over `calibration/runs/`).
8. Activity timeline page (aggregate over git log + draft/review/flag events from the existing action timeline data).

The depgraph and logigraph CLIs don't need to change. All new computation lives in graphui's loader and in the framework `reconcile.py` (for embeddings only).
