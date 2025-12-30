#!/usr/bin/env python
import ast
import sys
from pathlib import Path
from typing import List, Tuple

TARGET_FILES = [
    Path("webapp/services/pipeline_runner.py"),
    Path("webapp/services/job_manager.py"),
    Path("database/store.py"),
]

SAFE_CALLS = {"jsonable_encoder", "_json_safe"}


class SupabaseVisitor(ast.NodeVisitor):
    def __init__(self, filename: Path) -> None:
        self.filename = filename
        self.issues: List[Tuple[int, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        # Detect supabase.table(...).update/insert/upsert(...)
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in {"update", "insert", "upsert"}:
            if isinstance(func.value, ast.Call) and isinstance(func.value.func, ast.Attribute):
                if func.value.func.attr == "table":
                    payload_expr = None
                    if node.args:
                        payload_expr = node.args[0]
                    else:
                        for kw in node.keywords:
                            if kw.arg in (None, "values", "data"):
                                payload_expr = kw.value
                                break

                    if payload_expr is not None and not self._is_safe(payload_expr):
                        self.issues.append(
                            (
                                node.lineno,
                                f"Potential JSON-unsafe payload passed to {func.attr}() — wrap with jsonable_encoder/_json_safe",
                            )
                        )
        self.generic_visit(node)

    def _is_safe(self, expr: ast.AST) -> bool:
        # jsonable_encoder(...) or _json_safe(...) calls are considered safe
        if isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name) and expr.func.id in SAFE_CALLS:
                return True
            if isinstance(expr.func, ast.Attribute) and expr.func.attr in SAFE_CALLS:
                return True
        return False


def lint_file(path: Path) -> List[Tuple[int, str]]:
    try:
        src = path.read_text()
    except FileNotFoundError:
        return []

    tree = ast.parse(src, filename=str(path))
    visitor = SupabaseVisitor(path)
    visitor.visit(tree)
    return visitor.issues


def main() -> int:
    issues_found = False
    for path in TARGET_FILES:
        issues = lint_file(path)
        for lineno, msg in issues:
            issues_found = True
            print(f"{path}:{lineno}: {msg}")

    if issues_found:
        print("Supabase payload safety check FAILED")
        return 1
    print("Supabase payload safety check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
