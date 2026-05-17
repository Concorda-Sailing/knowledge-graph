# Dossier Format

A dossier is the human/LLM-curated companion to a node JSON file. Where the node captures *structure* (who calls whom, what shape, what file), the dossier captures *intent* (why it exists, what invariants hold, what surprises lurk).

Dossiers live at `depgraph/dossiers/<kind>/<id-slug>.md` and are pointed at by the node's `dossier` field.

## Required frontmatter

```yaml
---
node_id: POST::/api/invite/{code}/accept
node_kind: endpoint
feature: invites
last_reviewed: 2026-05-09
last_reviewed_against_hash: 8c2fa1...
status: current        # current | stale | unreviewed
---
```

`last_reviewed_against_hash` pins the dossier to a specific `structural_hash`. When the structural hash changes, the dossier is auto-marked `stale` and surfaces with a warning in the next PreToolUse injection. See **DRIFT.md scenario 3**.

## Required sections

```markdown
## Purpose
One-paragraph plain-English answer to "what is this for and why does it exist?" Include the user-visible behavior, not just the technical contract.

## Invariants
Bulleted list of things that must remain true. Examples:
- Token lookup is by SHA-256 hash of the raw token; the raw token never lives in the database.
- Expired or revoked invites must 404, not 410 — the UI treats them identically and we don't want to leak that the token was once valid.
- Accepting a `pending` invite creates a Membership row and deletes the PendingInvite in the same transaction.

## Gotchas
What has bitten us. Past incidents. Subtle ordering. Anything a reader would only learn the hard way.

## Cross-cutting concerns
Auth, rate limits, feature flags, websocket events emitted, audit log entries, side-effects on other features.

## External consumers
Shipped iOS app versions, integrations, anything outside the repo that depends on this. (Mirror what's in node JSON `external_consumers`, but explain the impact.)

## Open questions
Things we know we don't know. Future work tagged here.
```

## Optional sections

- **Migration history** — for endpoints that have shipped breaking changes; record the version cutover.
- **Performance notes** — known slow paths, indexes that matter.
- **Related dossiers** — links to neighbor nodes worth reading together.

## Tone

Write like an on-call note to your future self at 2am. Plain, short, factual. No marketing voice. No restating what the code obviously does.

## Lifecycle

| Event | What happens to the dossier |
|---|---|
| Node first extracted | Dossier auto-stubbed with `status: unreviewed`, only Purpose section pre-filled from the docstring/JSDoc. |
| Structural hash unchanged | Dossier carries forward as-is. |
| Structural hash changes | Dossier marked `stale`. PreToolUse injection prepends "⚠ structure drifted since last review" before the dossier body. |
| Human/LLM updates dossier | Bump `last_reviewed`, set `last_reviewed_against_hash` to current hash, set `status: current`. |
| Node deleted | Dossier moves to `dossiers/_archive/` with a tombstone line at top. Never silently deleted — past dossiers are useful for postmortems. |
