"""Pydantic schemas for Carbon MCP request/response contracts."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Language(str, Enum):
    python = "python"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    code: str = Field(..., description="Source code to analyze")
    language: Language = Field(Language.python, description="Programming language")
    filename: Optional[str] = Field(None, description="Optional filename for context")


# ---------------------------------------------------------------------------
# Response components
# ---------------------------------------------------------------------------

class Hotspot(BaseModel):
    line: int = Field(..., description="1-based line number of the issue")
    type: str = Field(..., description="Hotspot category, e.g. 'nested_loop'")
    description: str = Field(..., description="Human-readable description")
    severity: Severity


class Suggestion(BaseModel):
    hotspot_type: str = Field(..., description="The hotspot type this suggestion targets")
    description: str = Field(..., description="Short summary of the suggestion")
    guidance: str = Field(..., description="Actionable guidance or pseudocode")


class Emissions(BaseModel):
    estimated_co2_kg: float = Field(..., description="Rough CO₂ estimate in kilograms")
    energy_kwh: float = Field(..., description="Estimated energy in kWh")
    confidence: Confidence = Field(Confidence.low, description="Confidence of the estimate")


class AnalyzeResponse(BaseModel):
    emissions: Emissions
    hotspots: list[Hotspot]
    suggestions: list[Suggestion]
