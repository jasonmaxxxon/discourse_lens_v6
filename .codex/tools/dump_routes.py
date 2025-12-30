#!/usr/bin/env python3
"""
Static route extractor for FastAPI-like code.
- Scans Python files (default under webapp/) for decorators such as @app.get("/x") or @router.post("/y")
- Best-effort AST parsing; falls back to regex heuristics if AST fails.
- Outputs JSON to .codex/artifacts/endpoint_map.json and prints a readable summary.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


def parse_decorator(deco) -> Optional[Tuple[str, str]]:
    """Return (method, path) if decorator looks like router.get("/path")."""
    try:
        import ast

        if isinstance(deco, ast.Call):
            func = deco.func
            if isinstance(func, ast.Attribute) and func.attr in HTTP_METHODS:
                method = func.attr.upper()
                path = None
                if deco.args:
                    arg0 = deco.args[0]
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        path = arg0.value
                if path is None:
                    for kw in deco.keywords or []:
                        if kw.arg in ("path", "url"):
                            if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                                path = kw.value.value
                if path:
                    return method, path
    except Exception:
        return None
    return None


def scan_file_ast(path: Path) -> List[Dict[str, str]]:
    import ast

    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return []

    routes: List[Dict[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for deco in node.decorator_list:
                parsed = parse_decorator(deco)
                if parsed:
                    method, route_path = parsed
                    routes.append(
                        {
                            "method": method,
                            "path": route_path,
                            "function": node.name,
                            "file": str(path),
                            "line": node.lineno,
                        }
                    )
    return routes


REGEX_PATTERN = re.compile(r"@(router|app)\.(get|post|put|delete|patch)\((['\"])(.+?)\3")


def scan_file_regex(path: Path) -> List[Dict[str, str]]:
    routes: List[Dict[str, str]] = []
    try:
        for i, line in enumerate(path.read_text().splitlines(), start=1):
            m = REGEX_PATTERN.search(line)
            if m:
                method = m.group(2).upper()
                route_path = m.group(4)
                routes.append(
                    {
                        "method": method,
                        "path": route_path,
                        "function": "?",
                        "file": str(path),
                        "line": i,
                    }
                )
    except Exception:
        pass
    return routes


def dedupe(routes: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    deduped = []
    for r in routes:
        key = (r["method"], r["path"], r["file"], r["line"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped


def main():
    parser = argparse.ArgumentParser(description="Dump FastAPI routes without running the server.")
    parser.add_argument("--root", default="webapp", help="Root directory to scan (default: webapp)")
    parser.add_argument("--out", default=".codex/artifacts/endpoint_map.json", help="Output JSON path")
    args = parser.parse_args()

    root = Path(args.root)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    routes: List[Dict[str, str]] = []
    py_files = list(root.rglob("*.py"))
    for f in py_files:
        ast_routes = scan_file_ast(f)
        routes.extend(ast_routes)
        if not ast_routes:
            routes.extend(scan_file_regex(f))

    routes = dedupe(routes)
    out_path.write_text(json.dumps({"routes": routes}, indent=2))

    print(f"[dump_routes] scanned {len(py_files)} files, found {len(routes)} routes")
    for r in routes[:30]:
        print(f"- {r['method']:6s} {r['path']:35s} ({r['file']}:{r['line']})")
    if len(routes) > 30:
        print(f"... ({len(routes)-30} more)")


if __name__ == "__main__":
    main()
