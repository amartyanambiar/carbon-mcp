"""MCP stdio server for Carbon analysis tools."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from core.engine import Engine
from server.schemas import Language

mcp = FastMCP("carbon-mcp")
_engine = Engine()


def _to_language(value: str) -> Language:
    """Normalize user-provided language to the enum used by the engine."""
    try:
        return Language(value.lower())
    except ValueError as exc:
        supported = ", ".join(lang.value for lang in Language)
        raise ValueError(f"Unsupported language '{value}'. Supported: {supported}") from exc


@mcp.tool()
def analyze_code(code: str, language: str = "python") -> dict:
    """Analyze source code for carbon-inefficient patterns and return estimates."""
    response = _engine.analyze(code=code, language=_to_language(language))
    return response.model_dump(mode="json")


def main() -> None:
    """Run the MCP server over stdio for host clients such as VS Code Copilot."""
    mcp.run()


if __name__ == "__main__":
    main()