"""Carbon MCP CLI.

Usage
-----
    carbon analyze path/to/file.py
    carbon analyze path/to/file.py --language python
    carbon serve                           # start the API server
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from core.engine import Engine
from server.schemas import AnalyzeResponse, Language

app = typer.Typer(
    name="carbon",
    help="Analyze source code for carbon-inefficient patterns.",
    add_completion=False,
)

console = Console()
_engine = Engine()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _render_response(response: AnalyzeResponse, filename: str) -> None:
    """Pretty-print an AnalyzeResponse to the terminal."""

    # Emissions panel
    em = response.emissions
    console.print(
        Panel(
            f"[bold yellow]Estimated CO₂:[/bold yellow] {em.estimated_co2_kg:.2e} kg\n"
            f"[bold yellow]Energy:[/bold yellow]        {em.energy_kwh:.2e} kWh\n"
            f"[bold yellow]Confidence:[/bold yellow]    {em.confidence.value}",
            title=f"[bold green]Carbon MCP — {filename}[/bold green]",
            border_style="green",
        )
    )

    # Hotspots table
    if response.hotspots:
        table = Table(title="Hotspots", box=box.ROUNDED, show_lines=True)
        table.add_column("Line", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Severity", style="red")
        table.add_column("Description")

        for hs in response.hotspots:
            table.add_row(str(hs.line), hs.type, hs.severity.value, hs.description)

        console.print(table)
    else:
        console.print("[green]✓ No hotspots detected.[/green]")

    # Suggestions
    if response.suggestions:
        console.print("\n[bold underline]Suggestions[/bold underline]")
        for i, sug in enumerate(response.suggestions, 1):
            console.print(
                Panel(
                    f"[bold]{sug.description}[/bold]\n\n{sug.guidance}",
                    title=f"[yellow]{i}. {sug.hotspot_type}[/yellow]",
                    border_style="yellow",
                )
            )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@app.command()
def analyze(
    file: Path = typer.Argument(..., help="Path to the source file to analyze"),
    language: Language = typer.Option(Language.python, "--language", "-l", help="Language"),
) -> None:
    """Analyze a source file for carbon-inefficient patterns."""
    if not file.exists():
        console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(code=1)

    code = file.read_text(encoding="utf-8")
    try:
        response = _engine.analyze(code, language)
    except ValueError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    _render_response(response, filename=file.name)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload (dev mode)"),
) -> None:
    """Start the Carbon MCP API server."""
    try:
        import uvicorn  # noqa: PLC0415
    except ImportError:
        console.print("[red]uvicorn is not installed.[/red]  Run: pip install uvicorn")
        raise typer.Exit(code=1)

    console.print(f"[green]Starting Carbon MCP server on http://{host}:{port}[/green]")
    uvicorn.run("server.api:app", host=host, port=port, reload=reload)


@app.command("serve-mcp")
def serve_mcp() -> None:
    """Start the MCP stdio server for Copilot/agent integrations."""
    try:
        from server.mcp_server import main as mcp_main  # noqa: PLC0415
    except ImportError as exc:
        console.print("[red]MCP dependency is not installed.[/red]  Run: pip install mcp")
        raise typer.Exit(code=1) from exc

    mcp_main()


if __name__ == "__main__":
    app()
