"""logigraph validate subcommand — JSON-Schema check + dossier section check."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .context import Context
from ._shared import load_all_nodes, validate_json_schema

REQUIRED_RULE_DOSSIER_SECTIONS = (
    "## The rule",
    "## Why it exists",
    "## Decision table",
)
REQUIRED_DOMAIN_ROLE_DOSSIER_SECTIONS = (
    "## Plain definition",
    "## They can",
)


def _check_dossier_sections(dossier_path: Path, required: tuple[str, ...]) -> list[str]:
    """Return list of missing section headings."""
    if not dossier_path.exists():
        return list(required)
    text = dossier_path.read_text()
    return [s for s in required if s not in text]


def cmd_validate(args: argparse.Namespace, ctx: Context) -> int:
    domain_schema = ctx.tool_root / "schema" / "domain.schema.json"
    rule_schema = ctx.tool_root / "schema" / "rule.schema.json"
    process_schema = ctx.tool_root / "schema" / "process.schema.json"

    nodes = load_all_nodes(ctx)
    bad = 0
    stub_with_todo = 0

    for nid, (path, data) in nodes.items():
        kind = data.get("kind")
        if kind == "domain":
            err = validate_json_schema(data, domain_schema)
            if err:
                print(f"INVALID {path}: {err}", file=sys.stderr)
                bad += 1
                continue
            if data.get("subkind") == "role":
                dossier_rel = data.get("dossier")
                if dossier_rel:
                    missing = _check_dossier_sections(
                        ctx.LOGIGRAPH / dossier_rel,
                        REQUIRED_DOMAIN_ROLE_DOSSIER_SECTIONS,
                    )
                    if missing and data.get("definition_status") != "stub":
                        print(f"DOSSIER {path}: missing sections {missing}", file=sys.stderr)
                        bad += 1
        elif kind == "rule":
            err = validate_json_schema(data, rule_schema)
            if err:
                print(f"INVALID {path}: {err}", file=sys.stderr)
                bad += 1
                continue
            dossier_rel = data.get("dossier")
            if dossier_rel:
                missing = _check_dossier_sections(
                    ctx.LOGIGRAPH / dossier_rel, REQUIRED_RULE_DOSSIER_SECTIONS
                )
                if missing and data.get("definition_status") != "stub":
                    print(f"DOSSIER {path}: missing sections {missing}", file=sys.stderr)
                    bad += 1
        elif kind == "process":
            err = validate_json_schema(data, process_schema)
            if err:
                print(f"INVALID {path}: {err}", file=sys.stderr)
                bad += 1
                continue
            # Reference-integrity: every transition.to must be an existing step id.
            step_ids = {s["id"] for s in data.get("steps", [])}
            for step in data.get("steps", []):
                for tr in step.get("transitions", []) or []:
                    if tr["to"] not in step_ids:
                        print(
                            f"INVALID {path}: step '{step['id']}' transitions to "
                            f"'{tr['to']}' which is not a step in this process",
                            file=sys.stderr,
                        )
                        bad += 1
            # Dossier is intentionally optional for processes (pointer semantics).
            # No required-sections check.
        else:
            print(f"UNKNOWN KIND {path}: kind={kind}", file=sys.stderr)
            bad += 1

        if data.get("definition_status") == "stub":
            stub_with_todo += 1

    if bad:
        return 1
    print(f"all nodes valid ({len(nodes)} total, {stub_with_todo} stub)")
    return 0


def register(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("validate")
    p.set_defaults(func=cmd_validate)
