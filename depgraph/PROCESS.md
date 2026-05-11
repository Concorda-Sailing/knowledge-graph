# Edit Process

Rules of engagement once the dependency graph is wired up. These apply whether the editor is Claude or a human; Claude follows them by default through the `PreToolUse` / `Stop` hooks, but the rules are here so they can be reviewed, audited, and reasoned about independently of tooling.

## The contract, in one sentence

> Before changing a tracked node, read its dependents and its dossier; after changing it, re-extract and update the dossier if behavior shifted.

## Before edit

When `PreToolUse` fires on `Edit` / `Write` / `MultiEdit` against a tracked file:

1. The hook locates every node whose `source.path` matches the target file.
2. For each node, it injects:
   - **Dossier body** (truncated to ~200 lines per dossier; full text on request).
   - **Dependents list** with file:line for each call site.
   - **Drift warnings** if any apply (stale dossier, fuzzy edges, missing dossier, structural hash newer than `last_reviewed_against_hash`).
3. If injection fails (extractor missing, schema invalid, hook crash) the hook surfaces a loud error rather than silently no-op'ing. Editing without context is worse than knowing context is missing.

What I do with that context, in order:

1. **Read it.** Do not skim past the injection block — that is the entire reason the system exists.
2. **State the surface area.** Before proposing the edit, name the dependents I'm about to affect: "this changes the response shape of `POST /api/invite/{code}/accept`, which is consumed by `useAcceptInvite` (web) and `InviteAcceptScreen` (expo)."
3. **Decide whether the change crosses a boundary.** If it touches the request/response shape of an HTTP endpoint, the props of an exported component, or the return type of an exported hook, treat it as a breaking change: every dependent must be considered.
4. **If a dependent is shipped externally** (External consumers in the dossier), pause and confirm before proceeding. Mobile app users running an old build are not auto-updatable.

## During edit

- Do not delete a node file as a shortcut for "this endpoint is going away" — let the extractor reconcile it on the next regen so it goes through the orphan path with a paper trail.
- If you rename a route or a component, update the *source* — do not edit `nodes/*.json` by hand. The next regen will produce the right node id.
- If you discover something while editing that belongs in the dossier (an invariant, a gotcha), open the dossier and add it now. Dossiers go stale fastest the moment after a change.

## After edit

When `Stop` fires (end of turn or on save):

1. The hook collects the set of files touched in this session.
2. For each affected repo, it runs the relevant extractor.
3. The extractor uses **write-if-changed** semantics: per-node JSON is rewritten only if its stable view differs from disk. With no source change, regen produces zero file diffs.
4. The reconciler runs to refresh `nodes/_index/dependents.json` (the reverse-edge index) and `nodes/_meta.json` (corpus provenance + `regen_status: complete`).
5. If any extractor or reconcile fails, `_meta.regen_status` stays `in_progress`. The next PreToolUse renders a banner so I know the graph is torn before I trust it.

If a behavior change is real (not just whitespace), I am responsible for opening the dossier and updating it before the work is considered done. The structural hash being newer than `last_reviewed_against_hash` is exactly the signal that the dossier needs human/LLM attention.

## When adding a brand-new node

A new endpoint, component, or hook does not exist in the graph until extraction runs. The flow:

1. Write the code.
2. Run `bin/depgraph regen` (or let the Stop hook do it).
3. The extractor emits a node JSON; the reconciler auto-stubs a dossier with `status: unreviewed`.
4. Open the stub dossier and fill in **Purpose**, **Invariants**, **Gotchas**, **Cross-cutting concerns** before the PR is considered complete. Bump `status: current` and set `last_reviewed_against_hash` to the node's current hash.

A PR that adds nodes but leaves their dossiers stubbed should be flagged in review. Look for `status: unreviewed` in the dossier frontmatter.

## When deleting a node

Don't manually delete the node file. Delete the source code; let the next regen handle it via two mechanisms:

- **Filesystem orphan** — the source.path no longer exists. Reconciler archives the node with `_archived_reason: source_path_missing`.
- **Domain orphan** — the file remains but the symbol was removed. The extractor's manifest no longer claims this id; reconciler archives with `_archived_reason: domain_orphan_symbol_removed`.

Archived nodes go to `nodes/_archive/<kind>/<slug>.json` with a tombstone (`_archived_at`, `_archived_reason`). Dossiers are intentionally left in place — they're the only record of why the thing existed and are useful for postmortems.

## Working without the hook

If the hook is unavailable (running outside Claude Code, working in a different editor, hook disabled for debugging):

```bash
# Dump everything the hook would inject for a given file
bin/depgraph context <api-repo>/routers/invite.py

# Or, for a specific node id
bin/depgraph context "POST::/api/invite/{invite_code}/accept"
```

The CLI output is the same content the hook would inject. No special path.

## What this process does NOT replace

- **Code review.** Reverse edges show *who is affected*, not whether a change is correct.
- **Tests.** A green dependents list means the call sites compile, not that they still behave correctly. Run the affected tests.
- **Conversation with the user.** Cross-repo or cross-feature changes still require checking in, especially when external consumers are involved.

The graph reduces blind spots. It does not make changes safe on its own.
