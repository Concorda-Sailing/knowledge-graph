"""Recognize Python migration files and extract embedded SQL.

Migration files are Python modules that execute SQL strings against a
database connection. Concorda's convention: `migrations/NNN_<slug>.py`
with a `migrate()` function that calls `conn.execute(text("..."))`.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

from depgraph.lib.sql.parser import Operation, parse_operations


_ORDINAL_PREFIX = re.compile(r"^(\d+)_")


@dataclass
class MigrationOperation:
    """An Operation plus the source location it was extracted from."""
    operation: Operation
    source_line: int
    raw_sql: str

    # Convenience pass-throughs so tests can read `mo.kind` not `mo.operation.kind`
    @property
    def kind(self) -> str:
        return self.operation.kind

    @property
    def table(self) -> str | None:
        return self.operation.table


@dataclass
class MigrationFile:
    path: Path
    migration_order: int | None
    operations: list[MigrationOperation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def is_migration_file(path: Path) -> bool:
    """Path is in a migrations/ directory AND contains a text(...) call."""
    if "migrations" not in path.parts:
        return False
    if path.suffix != ".py":
        return False
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "text"):
            return True
    return False


def extract_migration(path: Path) -> MigrationFile:
    """Parse a migration file, extract every SQL string from text(...) calls,
    parse each into Operations, return MigrationFile with line metadata."""
    order = None
    m = _ORDINAL_PREFIX.match(path.name)
    if m:
        order = int(m.group(1))

    tree = ast.parse(path.read_text())
    result = MigrationFile(path=path, migration_order=order)

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "text"):
            continue
        arg = node.args[0] if node.args else None
        if arg is None:
            continue
        sql_text, dynamic_reason = _extract_string(arg)
        if dynamic_reason:
            result.warnings.append(
                f"line {node.lineno}: dynamic SQL skipped ({dynamic_reason})")
            continue
        ops = parse_operations(sql_text)
        for op in ops:
            result.operations.append(MigrationOperation(
                operation=op, source_line=node.lineno, raw_sql=sql_text,
            ))
    return result


def _extract_string(expr: ast.expr) -> tuple[str, str | None]:
    """Return (sql_text, dynamic_reason). dynamic_reason is non-None when
    the expression can't be reduced to a literal string at parse time."""
    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        return expr.value, None
    if isinstance(expr, ast.JoinedStr):  # f-string
        parts = []
        for v in expr.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                parts.append(v.value)
            else:
                return "", "f-string interpolation"
        return "".join(parts), None
    if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Add):
        l, lr = _extract_string(expr.left)
        r, rr = _extract_string(expr.right)
        if lr or rr:
            return "", lr or rr
        return l + r, None
    return "", "non-literal SQL expression"
