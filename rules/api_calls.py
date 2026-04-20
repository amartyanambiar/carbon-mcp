"""Rule: detect repeated / uncached HTTP API calls."""
from __future__ import annotations

import ast

from server.schemas import Hotspot, Severity

# Common HTTP client call patterns
_HTTP_MODULES = {"requests", "httpx", "aiohttp", "urllib"}
_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "request", "fetch"}


class _APICallVisitor(ast.NodeVisitor):
    """Collect Call nodes that look like HTTP requests."""

    def __init__(self) -> None:
        self.hotspots: list[Hotspot] = []
        self._loop_depth: int = 0

    # ------------------------------------------------------------------
    # Track loop context so we can raise severity for in-loop calls
    # ------------------------------------------------------------------

    def visit_For(self, node: ast.For) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_While(self, node: ast.While) -> None:
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    # ------------------------------------------------------------------
    # Detect HTTP calls
    # ------------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        if self._is_http_call(node.func):
            severity = Severity.high if self._loop_depth > 0 else Severity.medium
            context = " inside a loop — consider caching" if self._loop_depth > 0 else ""
            self.hotspots.append(
                Hotspot(
                    line=node.lineno,
                    type="repeated_api_call",
                    description=f"HTTP API call detected{context}.",
                    severity=severity,
                )
            )
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_http_call(func: ast.expr) -> bool:
        """Return True if the call looks like an HTTP request."""
        # requests.get(...) / httpx.post(...) etc.
        if isinstance(func, ast.Attribute):
            method = func.attr.lower()
            if method in _HTTP_METHODS:
                if isinstance(func.value, ast.Name) and func.value.id in _HTTP_MODULES:
                    return True
                # client.get(...) – attribute access on any variable
                if isinstance(func.value, ast.Name):
                    return method in _HTTP_METHODS
        # session.request(...)
        if isinstance(func, ast.Name) and func.id.lower() in _HTTP_METHODS:
            return True
        return False


def detect_api_calls(tree: ast.AST) -> list[Hotspot]:
    """Walk an AST and return hotspots for HTTP API calls."""
    visitor = _APICallVisitor()
    visitor.visit(tree)
    return visitor.hotspots
