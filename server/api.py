"""FastAPI application — Carbon MCP server."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, status

from core.engine import Engine
from server.schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="Carbon MCP",
    description=(
        "Model Context Protocol server that analyzes code and estimates "
        "its carbon impact, then suggests optimizations."
    ),
    version="0.1.0",
)

_engine = Engine()


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.post(
    "/analyze_code",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["analysis"],
    summary="Analyze source code for carbon-inefficient patterns",
)
def analyze_code(request: AnalyzeRequest) -> AnalyzeResponse:
    """Accept source code and return detected hotspots, emissions estimate,
    and actionable optimization suggestions.

    - **code**: Raw source code string
    - **language**: Programming language (default: `python`)
    - **filename**: Optional filename for display purposes
    """
    try:
        return _engine.analyze(request.code, request.language)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
