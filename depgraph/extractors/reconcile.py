#!/usr/bin/env python3
"""
reconcile.py — second-pass step that runs after every extractor.

The reconciler is the one place that thinks about the graph as a whole. It
does NOT mutate per-node JSON files (defect #1 fix): per-node files are owned
by the extractors and are bit-stable across regens. Reverse edges live in a
single derived index file written atomically.

Responsibilities, in order:

  1. Load every node JSON in nodes/**/*.json (skipping _archive/ and _index/).
  2. Build the reverse-dependency map in memory:
       for each node X with depends_on=[edge to Y], record (Y ← X) in by_target[Y].
  3. Write the map atomically to `nodes/_index/dependents.json` (tmp + rename).
     The file is sorted deterministically so it's bit-stable across regens that
     produce the same edges.
  4. Strip any leftover `dependents` field from per-node files (one-time cleanup
     for the v1→v2 transition; no-op once all extractors have re-run).
  5. Auto-stub dossiers for any node whose dossier file is missing.
  6. Detect orphans (source path missing) and stale dossiers (structural_hash
     drift). Reporting only — neither modifies the graph automatically.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TOOL_ROOT))
from lib.config import resolve_data_dir, primary_repo_path  # noqa: E402

DEPGRAPH = resolve_data_dir("DEPGRAPH_DATA_DIR")
NODES = DEPGRAPH / "nodes"
INDEX_DIR = NODES / "_index"
DEPENDENTS_INDEX = INDEX_DIR / "dependents.json"
INDEX_SCHEMA_VERSION = 1


def _is_node_file(path: Path) -> bool:
    """A node file lives in a kind subdirectory (endpoints/, models/, …). Any
    path component starting with `_` (e.g. _index/, _archive/, _meta.json,
    _staging/) is corpus metadata or operational state, not a node."""
    if path.name.startswith("_"):
        return False
    if any(p.startswith("_") for p in path.parts):
        return False
    return True


def load_all_nodes() -> dict[str, tuple[Path, dict]]:
    """Return id → (file_path, node_dict) for every authored node. Skips
    metadata files and archived nodes (anything under a `_*` path component)."""
    out: dict[str, tuple[Path, dict]] = {}
    for path in NODES.rglob("*.json"):
        if not _is_node_file(path):
            continue
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            print(f"WARN: invalid JSON {path}: {e}", file=sys.stderr)
            continue
        out[data["id"]] = (path, data)
    return out


def build_reverse_index(nodes: dict[str, tuple[Path, dict]]) -> tuple[dict[str, list[dict]], int]:
    """Walk every depends_on edge once and build target_id → [incoming edges].
    Returns (by_target, edge_count). Pure function — does NOT mutate nodes."""
    by_target: dict[str, list[dict]] = {}
    count = 0
    for src_id, (_, data) in nodes.items():
        for edge in data.get("depends_on", []) or []:
            target_id = edge.get("target")
            if not target_id:
                continue
            by_target.setdefault(target_id, []).append(
                {
                    "source": src_id,
                    "via": edge.get("via"),
                    "where": edge.get("where"),
                    "confidence": edge.get("confidence", "exact"),
                }
            )
            count += 1

    # Sort each list deterministically so the index file is bit-stable across
    # regens that produce the same edge set.
    for k in by_target:
        by_target[k].sort(key=lambda e: (e.get("source", ""), e.get("via", ""), e.get("where") or ""))

    return by_target, count


def write_dependents_index(by_target: dict[str, list[dict]], node_count: int, edge_count: int) -> tuple[bool, Path]:
    """Atomic write to nodes/_index/dependents.json. Returns (changed, path)."""
    from datetime import datetime, timezone

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": INDEX_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_head_primary(),
        "node_count": node_count,
        "edge_count": edge_count,
        # Keys sorted so by_target itself serializes deterministically.
        "by_target": {k: by_target[k] for k in sorted(by_target.keys())},
    }
    new_text = json.dumps(payload, indent=2, sort_keys=False) + "\n"

    # Bit-stability: if the existing index has the same content modulo the
    # generated_at timestamp, don't rewrite. This keeps the index file from
    # producing diffs on no-op regens.
    if DEPENDENTS_INDEX.exists():
        try:
            existing = json.loads(DEPENDENTS_INDEX.read_text())
            existing_stable = {k: v for k, v in existing.items() if k != "generated_at"}
            new_stable = {k: v for k, v in payload.items() if k != "generated_at"}
            if existing_stable == new_stable:
                return False, DEPENDENTS_INDEX
        except (OSError, json.JSONDecodeError):
            pass

    tmp = DEPENDENTS_INDEX.with_suffix(".json.tmp")
    tmp.write_text(new_text)
    tmp.replace(DEPENDENTS_INDEX)
    return True, DEPENDENTS_INDEX


LEGACY_FIELDS = ("dependents", "extracted_at", "git_commit")


def strip_legacy_fields(nodes: dict[str, tuple[Path, dict]]) -> int:
    """One-time cleanup: remove fields that have moved out of per-node JSON.
       - `dependents`    : moved to nodes/_index/dependents.json (defect #1)
       - `extracted_at`  : moved to nodes/_meta.json (defect #4)
       - `git_commit`    : moved to nodes/_meta.json (defect #4)
       After all extractors have re-run, this is a no-op every time. Idempotent."""
    cleaned = 0
    for path, data in nodes.values():
        if any(f in data for f in LEGACY_FIELDS):
            for f in LEGACY_FIELDS:
                data.pop(f, None)
            path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
            cleaned += 1
    return cleaned


CORPUS_META = NODES / "_meta.json"
META_SCHEMA_VERSION = 1


def write_corpus_meta(node_count: int, edge_count: int) -> tuple[bool, Path]:
    """Defect #4: corpus-level provenance in one file. Defect #2: writes
    `regen_status: complete` so the hook knows the corpus is consistent. If
    reconcile fails before reaching this call, the file is left in
    `regen_status: in_progress` (set by bin/depgraph at regen start) — the hook
    surfaces a banner so edits are made with full awareness of the torn state.
    Atomic via tmp+rename. Bit-stable when content (excluding generated_at) is
    unchanged."""
    from datetime import datetime, timezone

    payload = {
        "schema_version": META_SCHEMA_VERSION,
        "regen_status": "complete",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_head_primary(),
        "node_count": node_count,
        "edge_count": edge_count,
    }
    new_text = json.dumps(payload, indent=2, sort_keys=False) + "\n"

    if CORPUS_META.exists():
        try:
            existing = json.loads(CORPUS_META.read_text())
            existing_stable = {k: v for k, v in existing.items() if k not in ("generated_at", "started_at")}
            new_stable = {k: v for k, v in payload.items() if k not in ("generated_at", "started_at")}
            if existing_stable == new_stable:
                return False, CORPUS_META
        except (OSError, json.JSONDecodeError):
            pass

    CORPUS_META.parent.mkdir(parents=True, exist_ok=True)
    tmp = CORPUS_META.with_suffix(".json.tmp")
    tmp.write_text(new_text)
    tmp.replace(CORPUS_META)
    return True, CORPUS_META


def _git_head_primary() -> str | None:
    """Return the first 12 chars of the primary repo's git HEAD, or None.
    Primary repo is determined by [project] primary_repo in project.toml,
    falling back to the first [repos.*] table."""
    repo_path = primary_repo_path(DEPGRAPH)
    if repo_path is None:
        return None
    head = repo_path / ".git" / "HEAD"
    if not head.exists():
        return None
    try:
        ref = head.read_text().strip()
        if ref.startswith("ref:"):
            ref_path = repo_path / ".git" / ref.split(" ", 1)[1]
            if ref_path.exists():
                return ref_path.read_text().strip()[:12]
        return ref[:12]
    except OSError:
        return None


def detect_orphans(nodes: dict[str, tuple[Path, dict]]) -> list[str]:
    """Return ids of nodes whose source.path no longer exists. This catches
    the case where a whole file was deleted; defect #5's domain orphan check
    catches the finer case where the file remains but a symbol within it was
    removed."""
    orphans = []
    for nid, (_, data) in nodes.items():
        src = data.get("source", {})
        repo = src.get("repo")
        rel = src.get("path")
        if not repo or not rel:
            continue
        repo_path = Path.home() / repo
        if not (repo_path / rel).exists():
            orphans.append(nid)
    return orphans


MANIFEST_DIR = NODES / "_manifests"
ARCHIVE_DIR = NODES / "_archive"


def load_manifests() -> dict[str, set[str]]:
    """Defect #5: read every nodes/_manifests/<extractor>.json. Returns
    {extractor: {ids the extractor emitted this run}}.
    Manifest absence means the extractor didn't run — the reconciler must
    leave that extractor's nodes alone (preserving state during partial
    regens), not archive them."""
    out: dict[str, set[str]] = {}
    if not MANIFEST_DIR.exists():
        return out
    for f in MANIFEST_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("schema_version") != 1:
            continue
        out[data.get("extractor", f.stem)] = set(data.get("node_ids") or [])
    return out


def detect_domain_orphans(
    nodes: dict[str, tuple[Path, dict]],
    manifests: dict[str, set[str]],
) -> list[str]:
    """Defect #5: for each node whose extractor ran this round, check the
    manifest. If the node's id isn't claimed, the symbol was removed from
    the source file even though the file still exists. Archive candidate."""
    orphans: list[str] = []
    for nid, (_, data) in nodes.items():
        extractor_field = data.get("extractor", "")
        # Map "extract_api.py" → "extract_api" to match manifest names.
        extractor_key = extractor_field.replace(".py", "").replace(".ts", "")
        if extractor_key not in manifests:
            continue
        if nid not in manifests[extractor_key]:
            orphans.append(nid)
    return orphans


def archive_node(path: Path, data: dict, reason: str) -> Path:
    """Move a node JSON into nodes/_archive/<original-relative-path>, preserving
    its kind subdir. Adds a `_archived_at` and `_archived_reason` to the moved
    file so postmortems have provenance.
    Dossier files are intentionally left in place — they're keyed by id and
    the next regen will not auto-stub a replacement (no node, no stub trigger).
    Manual cleanup is preferred over auto-deletion of curated text."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(NODES)
    archive_path = ARCHIVE_DIR / rel
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    data["_archived_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"
    data["_archived_reason"] = reason
    archive_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    path.unlink()
    return archive_path


def detect_stale_dossiers(nodes: dict[str, tuple[Path, dict]]) -> list[str]:
    """Return ids whose dossier last_reviewed_against_hash != current structural_hash."""
    stale = []
    for nid, (_, data) in nodes.items():
        dossier_rel = data.get("dossier")
        if not dossier_rel:
            continue
        dossier_path = DEPGRAPH / dossier_rel
        if not dossier_path.exists():
            continue
        text = dossier_path.read_text()
        # Cheap parser for last_reviewed_against_hash in YAML frontmatter
        if "last_reviewed_against_hash:" not in text:
            stale.append(nid)
            continue
        for line in text.splitlines():
            if line.strip().startswith("last_reviewed_against_hash:"):
                pinned = line.split(":", 1)[1].strip().strip('"').strip("'")
                if pinned != data["structural_hash"]:
                    stale.append(nid)
                break
    return stale




DOSSIER_STUB_TEMPLATE = """---
node_id: {id}
node_kind: {kind}
feature: null
last_reviewed: {date}
last_reviewed_against_hash: {hash}
status: unreviewed
---

# {title}

## Purpose

_TODO: describe what this {kind} is for and why it exists, in plain English. The stub was auto-generated by reconcile.py — replace this and bump `status: current` once the dossier reflects reality._

## Invariants

_TODO: bulleted list of things that must remain true. See dossier.schema.md for guidance._

## Gotchas

_TODO: what has bitten us, surprising ordering, hard-learned lessons._

## Cross-cutting concerns

_TODO: auth, rate limits, websocket events, audit, side effects on other features._

## External consumers

_None known. (See node JSON `external_consumers` for the structured form.)_

## Open questions

_None recorded yet._
"""


def stub_missing_dossiers(nodes: dict[str, tuple[Path, dict]]) -> int:
    """Create an `unreviewed`-status stub dossier for every node that points
    at a dossier file that doesn't exist. Idempotent: existing dossiers are
    left alone."""
    from datetime import date

    today = date.today().isoformat()
    created = 0
    for nid, (_, data) in nodes.items():
        rel = data.get("dossier")
        if not rel:
            continue
        path = DEPGRAPH / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        body = DOSSIER_STUB_TEMPLATE.format(
            id=nid,
            kind=data.get("kind", "?"),
            date=today,
            hash=data.get("structural_hash", "unknown"),
            title=data.get("title") or nid,
        )
        path.write_text(body)
        created += 1
    return created


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()

    nodes = load_all_nodes()
    manifests = load_manifests()
    by_target, edge_count = build_reverse_index(nodes)
    fs_orphans = detect_orphans(nodes)
    domain_orphans = detect_domain_orphans(nodes, manifests)

    # Combine — fs_orphans (file deleted) ⊃ may overlap with domain_orphans
    # (symbol removed). Use union, dedup. Each archived node leaves the live
    # set so reverse-edge calc reflects current state.
    all_orphan_ids = list(dict.fromkeys(fs_orphans + domain_orphans))
    archived = 0
    if not args.report_only:
        for nid in all_orphan_ids:
            path, data = nodes[nid]
            reason = "source_path_missing" if nid in set(fs_orphans) else "domain_orphan_symbol_removed"
            try:
                archive_node(path, data, reason)
                archived += 1
                # Remove from live set so it doesn't contribute reverse edges
                # or get its dossier stubbed.
                nodes.pop(nid, None)
            except OSError as e:
                print(f"WARN: failed to archive {nid}: {e}", file=sys.stderr)

    # Re-run after archiving so the index reflects the live set.
    if archived > 0:
        by_target, edge_count = build_reverse_index(nodes)

    stubbed = stub_missing_dossiers(nodes) if not args.report_only else 0
    stale = detect_stale_dossiers(nodes)

    print(f"loaded:          {len(nodes)} nodes")
    print(f"reverse edges:   {edge_count}")
    print(f"manifests:       {len(manifests)} extractor(s) reporting")
    print(f"fs orphans:      {len(fs_orphans)}")
    print(f"domain orphans:  {len(domain_orphans)}")
    if archived:
        print(f"archived:        {archived} → nodes/_archive/")
    if stubbed:
        print(f"dossier stubs:   {stubbed} created")
    if all_orphan_ids:
        for oid in all_orphan_ids[:10]:
            print(f"  - {oid}")
        if len(all_orphan_ids) > 10:
            print(f"  ... and {len(all_orphan_ids) - 10} more")
    print(f"stale dossiers:  {len(stale)}")
    if stale:
        for sid in stale[:10]:
            print(f"  - {sid}")
        if len(stale) > 10:
            print(f"  ... and {len(stale) - 10} more")

    if not args.report_only:
        cleaned = strip_legacy_fields(nodes)
        if cleaned:
            print(f"legacy cleanup:  {cleaned} nodes had legacy fields stripped (dependents/extracted_at/git_commit)")
        changed, idx_path = write_dependents_index(by_target, len(nodes), edge_count)
        print(f"index:           {'updated' if changed else 'unchanged'} ({idx_path.relative_to(DEPGRAPH)})")
        meta_changed, meta_path = write_corpus_meta(len(nodes), edge_count)
        print(f"meta:            {'updated' if meta_changed else 'unchanged'} ({meta_path.relative_to(DEPGRAPH)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
