"""Unit tests for the Python AST analyzer and core engine."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from analyzer.python_analyzer import PythonAnalyzer
from core.engine import Engine
from server.api import app
from server.schemas import Language


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def analyzer() -> PythonAnalyzer:
    return PythonAnalyzer()


@pytest.fixture()
def engine() -> Engine:
    return Engine()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


# ---------------------------------------------------------------------------
# Analyzer — nested loops
# ---------------------------------------------------------------------------

NESTED_LOOP_CODE = """\
for i in range(10):
    for j in range(10):
        print(i, j)
"""

CLEAN_CODE = """\
lookup = {x: x * 2 for x in range(100)}
for key in lookup:
    print(lookup[key])
"""


def test_nested_loop_detected(analyzer: PythonAnalyzer) -> None:
    hotspots = analyzer.analyze(NESTED_LOOP_CODE)
    types = [h.type for h in hotspots]
    assert "nested_loop" in types


def test_clean_code_no_nested_loop(analyzer: PythonAnalyzer) -> None:
    hotspots = analyzer.analyze(CLEAN_CODE)
    assert not any(h.type == "nested_loop" for h in hotspots)


def test_nested_loop_severity_is_high(analyzer: PythonAnalyzer) -> None:
    hotspots = analyzer.analyze(NESTED_LOOP_CODE)
    nested = [h for h in hotspots if h.type == "nested_loop"]
    assert all(h.severity.value == "high" for h in nested)


# ---------------------------------------------------------------------------
# Analyzer — API calls
# ---------------------------------------------------------------------------

API_CALL_IN_LOOP = """\
import requests

for url in urls:
    resp = requests.get(url)
"""

API_CALL_OUTSIDE_LOOP = """\
import requests
resp = requests.get("https://example.com/data")
"""


def test_api_call_in_loop_detected(analyzer: PythonAnalyzer) -> None:
    hotspots = analyzer.analyze(API_CALL_IN_LOOP)
    assert any(h.type == "repeated_api_call" for h in hotspots)


def test_api_call_severity_high_inside_loop(analyzer: PythonAnalyzer) -> None:
    hotspots = analyzer.analyze(API_CALL_IN_LOOP)
    api_hs = [h for h in hotspots if h.type == "repeated_api_call"]
    assert all(h.severity.value == "high" for h in api_hs)


def test_api_call_outside_loop_is_medium(analyzer: PythonAnalyzer) -> None:
    hotspots = analyzer.analyze(API_CALL_OUTSIDE_LOOP)
    api_hs = [h for h in hotspots if h.type == "repeated_api_call"]
    assert all(h.severity.value == "medium" for h in api_hs)


# ---------------------------------------------------------------------------
# Engine — full pipeline
# ---------------------------------------------------------------------------

def test_engine_returns_suggestions_for_nested_loop(engine: Engine) -> None:
    result = engine.analyze(NESTED_LOOP_CODE, Language.python)
    suggestion_types = [s.hotspot_type for s in result.suggestions]
    assert "nested_loop" in suggestion_types


def test_engine_emissions_positive(engine: Engine) -> None:
    result = engine.analyze(NESTED_LOOP_CODE, Language.python)
    assert result.emissions.estimated_co2_kg > 0
    assert result.emissions.energy_kwh > 0


def test_engine_clean_code_zero_emissions(engine: Engine) -> None:
    result = engine.analyze(CLEAN_CODE, Language.python)
    assert result.emissions.estimated_co2_kg == 0.0


def test_engine_unknown_language_raises(engine: Engine) -> None:
    with pytest.raises(ValueError, match="No analyzer registered"):
        engine.analyze("print('hi')", "ruby")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# API — HTTP endpoints
# ---------------------------------------------------------------------------

def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_code_endpoint_nested_loop(client: TestClient) -> None:
    resp = client.post("/analyze_code", json={"code": NESTED_LOOP_CODE})
    assert resp.status_code == 200
    data = resp.json()
    assert "emissions" in data
    assert "hotspots" in data
    assert "suggestions" in data
    assert any(h["type"] == "nested_loop" for h in data["hotspots"])


def test_analyze_code_endpoint_clean_code(client: TestClient) -> None:
    resp = client.post("/analyze_code", json={"code": CLEAN_CODE})
    assert resp.status_code == 200
    data = resp.json()
    assert data["hotspots"] == []
