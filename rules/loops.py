"""Rule: detect nested for/while loops — O(n²) hotspot."""
from __future__ import annotations

import ast
from typing import Optional

from server.schemas import Hotspot, Severity


def _loop_line(node: ast.AST) -> int:
    return getattr(node, "lineno", 0)


def _is_loop(node: ast.AST) -> bool:
    return isinstance(node, (ast.For, ast.While))


def _find_nested_loops(
    node: ast.AST,
    depth: int = 0,
    parent_line: Optional[int] = None,
    results: Optional[list[Hotspot]] = None,
) -> list[Hotspot]:
    if results is None:
        results = []

    for child in ast.iter_child_nodes(node):
        if _is_loop(child):
            if depth >= 1:
                # This loop is nested inside at least one other loop
                results.append(
                    Hotspot(
                        line=_loop_line(child),
                        type="nested_loop",
                        description=(
                            f"Nested loop detected (depth {depth + 1}). "
                            "This may result in O(n²) or worse complexity."
                        ),
                        severity=Severity.high if depth == 1 else Severity.medium,
                    )
                )
            _find_nested_loops(child, depth + 1, _loop_line(child), results)
        else:
            _find_nested_loops(child, depth, parent_line, results)

    return results


def detect_nested_loops(tree: ast.AST) -> list[Hotspot]:
    """Walk an AST and return hotspots for every nested loop found."""
    return _find_nested_loops(tree)
