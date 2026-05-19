"""depgraph dossier lifecycle subcommand handlers.

Four commands grouped here because they share the `_dossier_state` helper
and all operate on the same dossier frontmatter schema:

  dossier-rank     — rank unreviewed/stale nodes by leverage
  dossier-draft    — prepare LLM-drafting context bundle (prompt to stdout)
  dossier-finalize — save a drafted body file to canonical path
  dossier-bump     — bump a dossier's status after human review
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Make depgraph/lib/config.py importable.
_DEPGRAPH_LIB = Path(__file__).resolve().parents[1]
if str(_DEPGRAPH_LIB) not in sys.path:
    sys.path.insert(0, str(_DEPGRAPH_LIB))
from depgraph.lib.config import load_project_config, repo_for_basename  # noqa: E402

from ._shared import load_dependents_index, find_nodes_for_target, dossier_state
from .context import Context


def _dossier_state(node: dict, ctx: Context) -> str:
    """Thin adapter so call sites keep their ctx-flavored signature."""
    return dossier_state(node, ctx.DEPGRAPH)


def _commits_touching(rel_path: str, repo: str, ctx: Context, days: int = 30) -> int:
    """Count commits in the last `days` that touched this file. Uses git log
    in the source repo. Returns 0 if anything goes wrong (no repo, file
    untracked, etc.). Resolves repo basename → checkout path via
    project.toml."""
    info = repo_for_basename(ctx.DEPGRAPH, repo)
    if info is None:
        return 0
    repo_root = info["path"]
    if not (repo_root / ".git").exists():
        return 0
    try:
        out = subprocess.run(
            ["git", "log", f"--since={days}.days.ago", "--oneline", "--", rel_path],
            cwd=str(repo_root),
            capture_output=True, text=True, timeout=10,
        )
        return len([l for l in out.stdout.splitlines() if l.strip()])
    except (OSError, subprocess.SubprocessError):
        return 0


def _tier_of(fan_out: int) -> str:
    if fan_out >= 10:
        return "A"
    if fan_out >= 3:
        return "B"
    return "C"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def cmd_dossier_rank(args: argparse.Namespace, ctx: Context) -> int:
    """Rank unreviewed nodes by importance, so the next dossier batch is
    chosen by leverage rather than alphabetical accident. Default scoring:
    fan_out + 2 * commits_30d (recent activity weighted slightly higher
    since recently-edited code is also more likely to be edited next)."""
    deps_idx = load_dependents_index(ctx)

    rows = []
    for node_file in ctx.NODES.rglob("*.json"):
        if node_file.name.startswith("_") or any(p.startswith("_") for p in node_file.parts):
            continue
        try:
            data = json.loads(node_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        nid = data.get("id")
        if not nid:
            continue
        state = _dossier_state(data, ctx)
        if args.only_stale:
            if state != "stale":
                continue
        elif args.only_unreviewed and state != "unreviewed":
            # `regen` stubs every non-trivial node with `status: unreviewed`
            # (#40), so a clean corpus has no `missing` state to worry about.
            # `missing` is a true alarm — surfaced via `depgraph health` —
            # not a routine on-ramp state, so we no longer fold it into
            # `--only-unreviewed`.
            continue
        fan_out = len(deps_idx.get(nid) or [])
        tier = _tier_of(fan_out)
        if args.tier and tier != args.tier:
            continue
        # Skip test nodes from rank by default — test dossiers are rarely
        # worth manual review (one-line "exercises X" suffices). Toggle
        # --include-tests to surface them.
        kind = data.get("kind", "")
        if kind == "test" and not args.include_tests:
            continue
        src = data.get("source") or {}
        repo = src.get("repo")
        rel = src.get("path")
        commits_30d = _commits_touching(rel, repo, ctx, days=30) if (repo and rel) else 0
        score = fan_out + 2 * commits_30d
        rows.append({
            "score": score,
            "fan_out": fan_out,
            "commits_30d": commits_30d,
            "tier": tier,
            "kind": kind,
            "state": state,
            "id": nid,
            "src": f"{repo}/{rel}" if (repo and rel) else "—",
        })

    rows.sort(key=lambda r: -r["score"])
    if args.limit:
        rows = rows[: args.limit]

    print(f"{'#':>4}  {'fan':>4}  {'30d':>4}  {'tier':<4}  {'kind':<10}  {'state':<10}  {'id'}")
    print("-" * 100)
    for i, r in enumerate(rows, 1):
        print(
            f"{i:>4}  {r['fan_out']:>4}  {r['commits_30d']:>4}  {r['tier']:<4}  "
            f"{r['kind']:<10}  {r['state']:<10}  {r['id']}"
        )
    print(f"\n  total: {len(rows)} nodes")
    return 0


def cmd_dossier_draft(args: argparse.Namespace, ctx: Context) -> int:
    """Prepare an LLM-drafting context bundle for one node. Outputs a
    structured prompt with source code, dependents, recent git history,
    and a strict authoring template. The user (or current Claude session)
    feeds this into the Agent tool, saves the response to the dossier
    path printed at the end, and bumps frontmatter status to llm_drafted.

    v2 will fully automate the agent invocation; v1 is two-step so
    each draft can be eyeballed before landing."""
    # Find the node by id or by file path
    matches = find_nodes_for_target(ctx, args.target)
    if not matches:
        print(f"no nodes match: {args.target}", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"multiple nodes match {args.target}; refine:", file=sys.stderr)
        for m in matches:
            try:
                d = json.loads(m.read_text())
                print(f"  {d['id']}", file=sys.stderr)
            except (OSError, json.JSONDecodeError):
                pass
        return 1

    node = json.loads(matches[0].read_text())
    nid = node["id"]
    src = node.get("source") or {}
    repo, rel, line = src.get("repo"), src.get("path"), src.get("line") or 1
    end_line = src.get("end_line") or (line + 60)
    repo_info = repo_for_basename(ctx.DEPGRAPH, repo) if repo else None

    # Tools mode = --auto + --tools. The thin prompt path expects the
    # model to fetch source/deps/history via the agent loop instead of
    # eating it pre-loaded. Skips the heavy gather entirely.
    auto = bool(getattr(args, "auto", False))
    tools_mode = auto and bool(getattr(args, "tools", False))

    # Cheap counts the thin prompt still needs (so the model knows
    # how many to fetch, and what file/line window to read).
    deps_idx = load_dependents_index(ctx)
    deps = deps_idx.get(nid) or []
    n_deps = len(deps)
    read_start = max(1, line - 5)
    read_end = end_line + 5

    src_excerpt = "(skipped: tools mode)" if tools_mode else "(unavailable)"
    deps_str = "(skipped: tools mode — call `dependents_of`)" if tools_mode else "  (none)"
    deps_more = ""
    git_log = "(skipped: tools mode — call `recent_history`)" if tools_mode else "(unavailable)"
    adj_str = "(skipped: tools mode)" if tools_mode else "  (none reviewed yet in this module)"
    rules_str = "  (none)"

    if not tools_mode:
        # Full pre-load: rich prompt for --auto without --tools and for
        # the non-auto "print prompt to stdout for a human to feed in"
        # workflow. Both consume the same baked-in context.
        if repo_info and rel:
            full = repo_info["path"] / rel
            if full.exists():
                try:
                    lines = full.read_text().splitlines()
                    start = max(0, line - 10)
                    end = min(len(lines), line + 70)
                    numbered = [f"{i+1:>5}  {l}" for i, l in enumerate(lines[start:end], start=start)]
                    src_excerpt = "\n".join(numbered)
                except OSError:
                    pass

        deps_str = "\n".join(
            f"  - {d.get('source','?')}  (via {d.get('via','?')}, {d.get('confidence','?')}, {d.get('where','—')})"
            for d in deps[:15]
        ) or "  (none)"
        deps_more = f"  ... +{len(deps) - 15} more" if len(deps) > 15 else ""

        if repo_info and rel:
            try:
                out = subprocess.run(
                    ["git", "log", "-15", "--oneline", "--", rel],
                    cwd=str(repo_info["path"]),
                    capture_output=True, text=True, timeout=10,
                )
                git_log = out.stdout.strip() or "(no recent commits)"
            except (OSError, subprocess.SubprocessError):
                pass

        # Adjacent dossiers — siblings in same module, only ones already
        # reviewed (current) so we don't propagate stub style
        adj_dossiers = []
        if repo and rel:
            same_dir_prefix = "/".join(rel.split("/")[:-1])
            for nf in ctx.NODES.rglob("*.json"):
                if nf.name.startswith("_") or any(p.startswith("_") for p in nf.parts):
                    continue
                try:
                    d = json.loads(nf.read_text())
                except (OSError, json.JSONDecodeError):
                    continue
                s = d.get("source") or {}
                if s.get("repo") != repo:
                    continue
                sp = s.get("path", "") or ""
                if not sp.startswith(same_dir_prefix):
                    continue
                if d.get("id") == nid:
                    continue
                if _dossier_state(d, ctx) != "current":
                    continue
                dossier_path = ctx.DEPGRAPH / (d.get("dossier") or "")
                if dossier_path.exists():
                    adj_dossiers.append((d["id"], dossier_path))
        adj_str = "\n".join(
            f"  - {nid_a}: see {p.relative_to(ctx.DEPGRAPH)}" for nid_a, p in adj_dossiers[:5]
        ) or "  (none reviewed yet in this module)"

        # Logigraph rules claiming this node — only useful with the rich
        # prompt; the tools-mode model can fetch this separately if we
        # ever expose a `rules_for_node` tool.
        rules_claiming = []
        cfg = load_project_config(ctx.DEPGRAPH)
        from kg.shared.env import LOGIGRAPH_DATA_DIR
        logigraph_dir_str = (
            os.environ.get(LOGIGRAPH_DATA_DIR)
            or (cfg.get("logigraph") or {}).get("data_dir")
        )
        by_code_idx = (
            Path(logigraph_dir_str).expanduser() / "nodes" / "_index" / "by_code.json"
            if logigraph_dir_str
            else None
        )
        if by_code_idx is not None and by_code_idx.exists():
            try:
                idx = json.loads(by_code_idx.read_text())
                rules_claiming = idx.get("by_target", {}).get(nid, [])
            except (OSError, json.JSONDecodeError):
                pass
        rules_str = "\n".join(f"  - {r}" for r in rules_claiming) or "  (none)"

    # Build the prompt
    dossier_path = ctx.DEPGRAPH / (node.get("dossier") or "")

    if tools_mode:
        prompt = _build_thin_prompt(
            nid=nid, node=node, repo=repo, rel=rel, line=line,
            read_start=read_start, read_end=read_end, n_deps=n_deps,
            dossier_path=dossier_path, ctx=ctx,
        )
    else:
        prompt = _build_full_prompt(
            nid=nid, node=node, repo=repo, rel=rel, line=line,
            src_excerpt=src_excerpt, deps_str=deps_str, deps_more=deps_more,
            n_deps=n_deps, git_log=git_log, adj_str=adj_str, rules_str=rules_str,
            dossier_path=dossier_path, ctx=ctx,
        )

    if not auto:
        print(prompt)
        print("\n---")
        print(f"# After authoring, save the response with:")
        print(f"#   bin/depgraph dossier-finalize {nid} <transcript-file>")
        return 0

    # --auto: hand the prompt to a configured summarizer model and write
    # the result straight to the canonical dossier path.
    try:
        from depgraph.lib.summarizer import (
            build_client,
            builtin_tool_definitions,
            builtin_tool_handlers,
            load_models,
            run_agent,
        )
        from depgraph.lib.summarizer.tools import ToolContext
    except ImportError as e:
        print(f"--auto requires the summarizer module: {e}", file=sys.stderr)
        return 1

    try:
        summarizer_cfg = load_models(ctx.DEPGRAPH)
    except (KeyError, ValueError) as e:
        print(f"summarizer config error: {e}", file=sys.stderr)
        return 1

    if not summarizer_cfg.models:
        print(
            "no [summarizer.models.*] configured in project.toml — add a "
            "model entry first; see depgraph/lib/summarizer/config.py for "
            "the schema.",
            file=sys.stderr,
        )
        return 1

    try:
        model_cfg = summarizer_cfg.get(getattr(args, "model", None))
    except KeyError as e:
        print(f"summarizer: {e}", file=sys.stderr)
        return 1

    client = build_client(model_cfg)

    tools_defs = None
    tools_handlers = None
    if getattr(args, "tools", False):
        # Build the tool context: deps index + node map keyed by id.
        deps_idx = load_dependents_index(ctx)
        nodes_by_id: dict[str, dict] = {}
        for nf in ctx.NODES.rglob("*.json"):
            if nf.name.startswith("_") or any(p.startswith("_") for p in nf.parts):
                continue
            try:
                d = json.loads(nf.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if "id" in d:
                nodes_by_id[d["id"]] = d
        # Resolve repo key → checkout path from project.toml.
        from depgraph.lib.config import project_repos
        repos = {k: info["path"] for k, info in project_repos(ctx.DEPGRAPH).items()}
        tctx = ToolContext(
            data_dir=ctx.DEPGRAPH,
            repos=repos,
            dependents_index=deps_idx,
            nodes_by_id=nodes_by_id,
        )
        tools_defs = builtin_tool_definitions()
        tools_handlers = builtin_tool_handlers(tctx)

    print(
        f"--- dossier-draft --auto: model={model_cfg.name} "
        f"spec={model_cfg.spec} tools={'on' if tools_defs else 'off'}",
        file=sys.stderr,
    )
    try:
        result = run_agent(
            client,
            user_prompt=prompt,
            tools=tools_defs,
            tool_handlers=tools_handlers,
            max_turns=int(getattr(args, "max_turns", None) or 64),
        )
    except Exception as e:
        print(f"summarizer call failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    body = (result.text or "").strip()
    if not body:
        print(
            f"summarizer returned empty body (stop_reason={result.stop_reason}, "
            f"turns={result.turns}); not writing dossier.",
            file=sys.stderr,
        )
        return 1

    _save_drafted_dossier(node=node, ctx=ctx, body=body, authored_by=[model_cfg.name])
    print(
        f"summarizer: {result.turns} turn(s), stop_reason={result.stop_reason}, "
        f"tokens={result.usage_totals}",
        file=sys.stderr,
    )
    return 0


# Grounding rules + section schema are identical in both prompt variants.
# Extracted as a constant so the two builders below stay short and so
# the rules themselves are easy to find and edit.
_GROUNDING_AND_SECTIONS = """## GROUNDING RULES (read before drafting)

These rules override your priors. Violating them makes the dossier
worse than empty.

1. **Only assert what your evidence supports.** Your evidence base is
   either the pre-loaded sections in this prompt or the results of
   tool calls you've made this turn. If a claim cannot be traced to
   one of those, do not write it.

2. **No invented commit hashes.** If you cite a commit, it MUST appear
   verbatim in your evidence (the "Recent commits" section, or a
   `recent_history` tool result). Do not invent SHAs. Quote the commit
   message verbatim. If you have no commit history, do not write
   anything in Gotchas that references git history.

3. **No invented callers, consumers, or integrations.** "External
   consumers" must be grounded in "Direct dependents" or a
   `dependents_of` tool result. If dependents is empty or only test
   files, write "None known from corpus." Do not list plausible-
   sounding routers, jobs, or webhooks.

4. **No invented exception types, return shapes, or error formats.**
   Read the actual source. If it raises `HTTPException`, say
   `HTTPException`, not `PermissionDenied`. Match identifiers exactly.

5. **No speculative performance, security, or scale claims** unless
   the source or commits contain evidence. Do not invent thresholds,
   benchmarks, or "occasional spikes."

6. **Prefer omission over invention.** Empty sections are fine.
   "None observed in corpus" or "Not visible from this excerpt" beats
   a confident fabrication. The dossier is read by future LLMs at
   edit time — wrong facts are worse than missing ones.

## Sections (write in this exact order)

## Purpose
~1 paragraph. What this node does and why it exists, grounded in the
source. Frame so a future Claude can make a decision. No filler. If
the source is too thin to support a purpose claim, say that explicitly.

## Invariants
Bulleted list of things that must remain true, each traceable to the
source or to a specific recent commit. No generic invariants
("must be idempotent", "must not modify state") unless the source
actually demonstrates them.

## Gotchas
What has bitten, grounded in recent commits (quote the line) or
visible in the source. Do not invent reverts, edge cases, or
historical incidents. If nothing is visible, write "None visible
from recent commits."

## Cross-cutting concerns
Auth, rate limits, audit, side effects on other features — only
those visible in the source or in dependent call sites. "Not visible
from this excerpt" is a valid entry per topic.

## External consumers
Grounded in dependents. If dependents is empty or only test files,
write "None known from corpus." Do not invent apps, jobs, webhooks,
or CLIs.

## Open questions
Unresolved design or implementation questions that surfaced from
reading the source/commits. Empty is fine. Before listing one,
check the architecture-synthesis probes below — many "open questions"
can be resolved by one more tool call.

## ARCHITECTURE SYNTHESIS (run before finalizing Open questions)

An open question is honest when human judgment is required; it's a
cop-out when a tool call would resolve it. Before you punt to Open
questions, do these three synthesis checks. State the answer in the
appropriate section above (Invariants, Gotchas, Cross-cutting) instead
of leaving the question dangling.

1. **Dead-field check.** Does the source declare a field whose
   comment/name/context suggests it's *legacy* (named `*_ids`,
   commented "kept for migration", retained for SQLite compat, etc.)?
   If so, you do not yet know if it's still live. Call `read_source`
   on the file again searching for write sites (`<field> =`), and call
   `dependents_of` to see if any consumer reads it. **Zero writers =
   dead column / migration ghost.** Say so in Invariants, name the
   replacement (the actual source of truth that current code uses).

2. **Multi-source-of-truth check.** If two parts of the codebase
   address the same concept (ownership, identity, active state, etc.)
   via *different mechanisms* — one via a column on this symbol, one
   via a join table, one via a `role`/`status` filter — they cannot
   both be authoritative. Find writers of each via `read_source`. The
   one with active writers is current; the other is legacy or
   intermediate. State the truth in Invariants. Do not list both
   without resolving which is current.

3. **Workflow synthesis.** If the dependents cluster around a related
   set of operations (e.g. `X_invite`, `X_promotion`, `X_removal`,
   `X_transfer`), don't enumerate them flatly under External consumers
   — synthesize the *workflow* under Cross-cutting concerns:
   "This symbol participates in the X lifecycle via the cluster of
   operations in <module>." Name the lifecycle, not just the files.

The point of a dossier is to surface architectural truth a future
Claude can act on, not to log what you couldn't figure out. If a tool
call can answer a question, the question goes in Invariants /
Gotchas / Cross-cutting *with the answer*, not in Open questions.

Quality bar: substantive AND grounded. A short, accurate dossier is
infinitely more valuable than a long fabricated one. "I cannot tell
from the available evidence" is a legitimate answer — but only after
the architecture-synthesis probes were actually run."""


def _build_thin_prompt(
    *,
    nid: str,
    node: dict,
    repo: Optional[str],
    rel: Optional[str],
    line: int,
    read_start: int,
    read_end: int,
    n_deps: int,
    dossier_path: Path,
    ctx: Context,
) -> str:
    """Tool-driven prompt: deliberately omits source/deps/git so the
    agent loop has to fetch via tools before drafting. Without the
    explicit MUST-call list, the model is content to draft from
    priors — see issue #48."""
    return f"""You are drafting a depgraph dossier for a code node. You
have tools and you MUST use them. This prompt deliberately does not
pre-load source, callers, or git history — fetching is the job.

# Node
- id: {nid}
- kind: {node.get("kind","?")}
- source: {repo}/{rel}:{line}
- structural_hash: {node.get("structural_hash","?")[:12]}
- direct dependents: {n_deps} recorded

# Required exploration (do this BEFORE writing prose)

You MUST call these tools at minimum. Skipping any of them means the
dossier will be wrong:

1. `read_source(repo="{repo}", path="{rel}", start_line={read_start}, end_line={read_end})`
   — see the actual symbol body. Adjust the window if too narrow.

2. `dependents_of(node_id="{nid}", limit=50)`
   — list who depends on this node. The prompt only tells you the
   count ({n_deps}); the tool returns the actual ids and call sites.

3. `recent_history(repo="{repo}", path="{rel}", limit=25)`
   — last commits touching this file. Commit messages are the source
   of truth for what bit recently. If empty, you have no Gotchas.

Then make additional calls as needed: `read_source` on dependent
files to verify call patterns; `node_info(node_id="...")` to inspect
a specific dependent's structure.

# Curiosity probes (drive deeper exploration before drafting)

These probes target the gap between "accurate but shallow" and "useful."
A correct purpose paragraph plus a list of callers is the floor; the
ceiling is finding the *non-obvious* thing a future Claude would want
to know. Answer each probe with a tool call or explicitly mark it
unanswerable. Do NOT guess.

1. **Sibling contrast.** Are there sibling symbols in the same file
   with similar names? (e.g. `require_auth` vs `require_session_auth`,
   `save_X` vs `delete_X`, getter/setter pairs, `_internal` variant
   alongside the public one.) Call `read_source` on the surrounding
   ±50 lines to see them. The most informative gotchas come from
   contrasts between near-twins that behave differently — note the
   contrast in Gotchas if it changes how the symbol should be used.

2. **Dependent diversity.** Pick 2 callers from different parts of
   the codebase (not two from the same module) and use
   `node_info` or `read_source` to see HOW they call this. Look for
   patterns: do some pass extra kwargs that others don't? Is one
   async and another sync? Is one wrapping it in a class method?
   Capture the dominant call pattern in Invariants if there is one,
   or note the variability in Open questions.

3. **Type-system check.** For any non-obvious type the symbol depends
   on (a class from this corpus, a `Mapped[X]` column, a custom
   exception), call `node_info` on that type. Often the real gotcha
   lives in how the type is constructed/cached/lazy-loaded, not in
   the function body itself. (Example: a function that takes an
   `AuthUser` may be safe in isolation but the gotcha lives in how
   `AuthUser.permissions` is computed and cached.)

4. **Hidden-history scan.** In `recent_history` output, look for
   commits whose subject doesn't mention the symbol by name but
   touches the file anyway — broad refactors, "fix X" without
   naming X. Those often introduce silent behavior changes. If you
   see one within the last ~10 commits, read its diff via
   `read_source` (around the line numbers in the commit) or flag it
   as an Open question.

5. **Implicit-contract check.** Does this symbol assume something
   about its caller that isn't in its signature? (Auth state, an
   open transaction, a specific role, a singleton being initialized,
   an env var being set.) If yes, name the assumption in Invariants
   and where it's enforced (or admit it isn't).

Skipping these probes makes the dossier accurate but shallow. The
point of a dossier is to surface what source alone doesn't carry —
that's almost always one of the above five.

# Authoring task

After exploration, write the dossier in this exact structure
(markdown headings, no frontmatter — the CLI adds frontmatter when
saving).

{_GROUNDING_AND_SECTIONS}

Output ONLY the dossier markdown body (no frontmatter, no
``` fences around the whole thing). The CLI will save to:

  {dossier_path.relative_to(ctx.DEPGRAPH)}
"""


def _build_full_prompt(
    *,
    nid: str,
    node: dict,
    repo: Optional[str],
    rel: Optional[str],
    line: int,
    src_excerpt: str,
    deps_str: str,
    deps_more: str,
    n_deps: int,
    git_log: str,
    adj_str: str,
    rules_str: str,
    dossier_path: Path,
    ctx: Context,
) -> str:
    """Pre-loaded prompt: bakes source, deps, git log, adjacent
    dossiers into the prompt itself. Used when the model has no tool
    access (one-shot --auto, or the print-to-stdout mode where a
    human will paste the prompt into another tool)."""
    return f"""You are drafting a depgraph dossier for a code node. The
dossier will be injected at edit time to give future LLM collaborators
the *intent* and *gotchas* that source code alone doesn't carry.

# Node
- id: {nid}
- kind: {node.get("kind","?")}
- source: {repo}/{rel}:{line}
- structural_hash: {node.get("structural_hash","?")[:12]}

# Source excerpt (around line {line})
```
{src_excerpt}
```

# Direct dependents ({n_deps} total)
{deps_str}
{deps_more}

# Recent commits touching this file (last 15)
```
{git_log}
```

# Adjacent reviewed dossiers in this module
{adj_str}

# Logigraph rules claiming this node
{rules_str}

# Authoring task

Write the dossier in this exact structure (markdown headings, no
frontmatter — the CLI adds frontmatter when saving).

{_GROUNDING_AND_SECTIONS}

Output ONLY the dossier markdown body (no frontmatter, no
``` fences around the whole thing). The CLI will save to:

  {dossier_path.relative_to(ctx.DEPGRAPH)}
"""


def _save_drafted_dossier(
    *,
    node: dict,
    ctx: Context,
    body: str,
    authored_by: list[str],
) -> Path:
    """Write a dossier body to the canonical path with `status: llm_drafted`
    frontmatter. Same shape as cmd_dossier_finalize emits — extracted so
    the --auto path can reuse it without going through argparse.
    """
    import datetime as _dt

    rel = node.get("dossier") or ""
    if not rel:
        raise ValueError(f"node {node.get('id')!r} has no dossier path")
    dossier_path = ctx.DEPGRAPH / rel
    today = _dt.date.today().isoformat()
    title = node.get("title") or node["id"].split("::")[-1]
    fm_lines = [
        "---",
        f"node_id: {node['id']}",
        f"node_kind: {node.get('kind','?')}",
        f"feature: {node.get('feature') or 'null'}",
        f"last_reviewed: {today}",
        f"last_reviewed_against_hash: {node.get('structural_hash')}",
        "status: llm_drafted",
    ]
    if authored_by:
        fm_lines.append("authored_by:")
        for a in authored_by:
            fm_lines.append(f"  - {a}")
    fm_lines.append("---")
    frontmatter = "\n".join(fm_lines) + "\n\n" + f"# {title}\n\n"
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text(frontmatter + body + "\n")
    print(f"wrote {dossier_path.relative_to(ctx.DEPGRAPH)}")
    _refresh_embeddings_for_node(node, ctx)
    return dossier_path


def cmd_dossier_finalize(args: argparse.Namespace, ctx: Context) -> int:
    """Save an LLM-drafted dossier from a transcript file to the
    appropriate path, with frontmatter set to llm_drafted."""
    matches = find_nodes_for_target(ctx, args.node_id)
    if not matches:
        print(f"no nodes match: {args.node_id}", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"multiple nodes match; refine the id", file=sys.stderr)
        return 1

    node = json.loads(matches[0].read_text())
    rel = node.get("dossier")
    if not rel:
        print(f"node has no dossier path", file=sys.stderr)
        return 1
    dossier_path = ctx.DEPGRAPH / rel

    body_file = Path(args.body_file)
    if not body_file.exists():
        print(f"body file not found: {body_file}", file=sys.stderr)
        return 1
    body = body_file.read_text().strip()

    import datetime as _dt
    today = _dt.date.today().isoformat()
    title = node.get("title") or node["id"].split("::")[-1]
    fm_lines = [
        "---",
        f"node_id: {node['id']}",
        f"node_kind: {node.get('kind','?')}",
        f"feature: {node.get('feature') or 'null'}",
        f"last_reviewed: {today}",
        f"last_reviewed_against_hash: {node.get('structural_hash')}",
        "status: llm_drafted",
    ]
    if args.authored_by:
        fm_lines.append("authored_by:")
        for a in args.authored_by:
            fm_lines.append(f"  - {a}")
    fm_lines.append("---")
    frontmatter = "\n".join(fm_lines) + "\n\n" + f"# {title}\n\n"
    dossier_path.parent.mkdir(parents=True, exist_ok=True)
    dossier_path.write_text(frontmatter + body + "\n")
    print(f"wrote {dossier_path.relative_to(ctx.DEPGRAPH)}")
    print(f"status: llm_drafted (review and bump to current when satisfied)")
    _refresh_embeddings_for_node(node, ctx)
    return 0


def cmd_dossier_bump(args: argparse.Namespace, ctx: Context) -> int:
    """Bump a dossier from llm_drafted/unreviewed to current after a human
    review pass. Updates the status line and refreshes last_reviewed +
    last_reviewed_against_hash to today and the node's current
    structural_hash."""
    matches = find_nodes_for_target(ctx, args.node_id)
    if not matches:
        print(f"no nodes match: {args.node_id}", file=sys.stderr)
        return 1
    if len(matches) > 1:
        print(f"multiple nodes match; refine the id", file=sys.stderr)
        return 1

    node = json.loads(matches[0].read_text())
    rel = node.get("dossier")
    if not rel:
        print(f"node has no dossier path", file=sys.stderr)
        return 1
    dossier_path = ctx.DEPGRAPH / rel
    if not dossier_path.exists():
        print(f"dossier file not found: {dossier_path}", file=sys.stderr)
        return 1

    text = dossier_path.read_text()
    if not text.startswith("---"):
        print(f"dossier missing frontmatter", file=sys.stderr)
        return 1
    end = text.index("\n---\n", 4)
    fm = text[4:end]
    body = text[end + 5:]

    import datetime as _dt
    today = _dt.date.today().isoformat()
    new_hash = node.get("structural_hash")
    out_lines = []
    seen_status = False
    seen_reviewed = False
    seen_reviewed_hash = False
    for line in fm.splitlines():
        s = line.strip()
        if s.startswith("status:"):
            out_lines.append(f"status: {args.status}")
            seen_status = True
        elif s.startswith("last_reviewed:"):
            out_lines.append(f"last_reviewed: {today}")
            seen_reviewed = True
        elif s.startswith("last_reviewed_against_hash:"):
            out_lines.append(f"last_reviewed_against_hash: {new_hash}")
            seen_reviewed_hash = True
        else:
            out_lines.append(line)
    if not seen_status:
        out_lines.append(f"status: {args.status}")
    if not seen_reviewed:
        out_lines.append(f"last_reviewed: {today}")
    if not seen_reviewed_hash:
        out_lines.append(f"last_reviewed_against_hash: {new_hash}")
    new_text = "---\n" + "\n".join(out_lines).strip("\n") + "\n---\n" + body
    dossier_path.write_text(new_text)
    print(f"bumped {dossier_path.relative_to(ctx.DEPGRAPH)} → status: {args.status}")
    _refresh_embeddings_for_node(node, ctx)
    return 0


def _refresh_embeddings_for_node(node: dict, ctx: Context) -> None:
    """Wrapper around `refresh_node_embeddings` that swallows missing
    dependencies. Lifecycle commands shouldn't fail when the embedding
    pipeline is unavailable (fastembed not installed, model load fails,
    or the corpus pre-dates the first full regen) — they just print a
    status line and continue.
    """
    try:
        from depgraph.extractors.reconcile import refresh_node_embeddings
    except ImportError:
        return
    try:
        status = refresh_node_embeddings(node, ctx.DEPGRAPH)
    except Exception as e:  # defensive: never block a successful write
        print(f"warning: embedding refresh raised {type(e).__name__}: {e}",
              file=sys.stderr)
        return
    if status == "ok":
        print("embedding index refreshed for this node")
    elif status == "failed":
        print(
            "warning: embedding refresh failed — node is on disk but "
            "search won't see it until the next full regen",
            file=sys.stderr,
        )
    # "skipped" is the common "no fastembed yet" / "no prior pass" case —
    # quiet on stdout to avoid flooding the auto-draft path with notes.


# ---------------------------------------------------------------------------
# register — NOT wired into bin/depgraph yet (Task 15)
# ---------------------------------------------------------------------------

def register(sub: argparse._SubParsersAction) -> None:
    """Add all 4 dossier subparsers to `sub`."""
    p_dr = sub.add_parser(
        "dossier-rank",
        help="Rank unreviewed/stale nodes by leverage (fan-out + recent-commit-frequency)",
    )
    p_dr.add_argument("--tier", choices=["A", "B", "C"], help="Filter by tier")
    p_dr.add_argument("--limit", type=int, default=50, help="Max rows (default 50)")
    # action='store_true' supplies default=False on its own. The earlier
    # `default=True` overrode that and made the flag a no-op — passed or
    # omitted, args.only_unreviewed was always True (#35).
    p_dr.add_argument(
        "--only-unreviewed", action="store_true",
        help="Filter to nodes whose dossier state is 'unreviewed' "
             "(stub awaiting first-pass review). Omit to rank every node.",
    )
    p_dr.add_argument("--only-stale", action="store_true")
    p_dr.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test nodes (default off — they rarely need full dossiers)",
    )
    p_dr.set_defaults(func=cmd_dossier_rank)

    p_dd = sub.add_parser(
        "dossier-draft",
        help="Prepare LLM-drafting context for one node (output a prompt; --auto to call a configured model)",
    )
    p_dd.add_argument("target", help="Node id or source file path")
    p_dd.add_argument(
        "--auto", action="store_true",
        help="Skip stdout; call a configured summarizer model and write the dossier directly.",
    )
    p_dd.add_argument(
        "--model", default=None,
        help="[--auto] Model key from [summarizer.models.*]; defaults to [summarizer].default_model "
             "or the first declared model.",
    )
    p_dd.add_argument(
        "--tools", action="store_true",
        help="[--auto] Enable tool use (agent loop). Without this, runs in one-shot mode.",
    )
    p_dd.add_argument(
        "--max-turns", dest="max_turns", type=int, default=None,
        help="[--auto --tools] Cap on agent round-trips (default 64). Hub nodes with many dependents and the architecture-synthesis probe can exceed 16 turns; the higher default lets them complete without truncation.",
    )
    p_dd.set_defaults(func=cmd_dossier_draft)

    p_df = sub.add_parser(
        "dossier-finalize",
        help="Save an LLM-drafted dossier body file to the canonical path",
    )
    p_df.add_argument("node_id")
    p_df.add_argument(
        "body_file",
        help="Path to file containing the dossier body markdown (no frontmatter)",
    )
    p_df.add_argument(
        "--authored-by",
        action="append",
        default=[],
        dest="authored_by",
    )
    p_df.set_defaults(func=cmd_dossier_finalize)

    p_db = sub.add_parser(
        "dossier-bump",
        help="Bump a dossier's status (e.g. llm_drafted → current) after a human review pass",
    )
    p_db.add_argument("node_id")
    p_db.add_argument("--status", default="current", help="New status (default: current)")
    p_db.set_defaults(func=cmd_dossier_bump)
