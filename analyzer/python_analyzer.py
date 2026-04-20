"""Python AST-based analyzer.

Runs all registered rules against parsed Python source code and
aggregates the resulting hotspots.
"""
from __future__ import annotations

import ast
from typing import Callable

from analyzer.base import BaseAnalyzer
from rules.api_calls import detect_api_calls
from rules.loops import detect_nested_loops
from server.schemas import Hotspot

# Each rule is a callable: (ast.AST) -> list[Hotspot]
# Add new rules here without touching any other module.
_RULES: list[Callable[[ast.AST], list[Hotspot]]] = [
    detect_nested_loops,
    detect_api_calls,
]


class PythonAnalyzer(BaseAnalyzer):
    """Analyzes Python source code using the built-in ``ast`` module."""

    language = "python"

    def analyze(self, code: str) -> list[Hotspot]:
        """Parse *code* with the Python AST and run all registered rules.

        Returns an empty list if the code cannot be parsed (syntax errors
        are surfaced as a single hotspot instead of crashing).
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return [
                Hotspot(
                    line=exc.lineno or 1,
                    type="syntax_error",
                    description=f"Syntax error: {exc.msg}",
                    severity="low",  # type: ignore[arg-type]
                )
            ]

        hotspots: list[Hotspot] = []
        for rule in _RULES:
            hotspots.extend(rule(tree))

        # Stable ordering by line number
        hotspots.sort(key=lambda h: h.line)
        return hotspots
