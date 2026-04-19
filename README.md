# Carbon MCP

> An MCP-style server that analyzes source code for carbon-inefficient patterns,
> estimates CO₂ emissions, and returns actionable optimization suggestions.

---

## Architecture

```
carbon-mcp/
├── server/
│   ├── api.py          # FastAPI application — POST /analyze_code, GET /health
│   └── schemas.py      # Pydantic request/response contracts
├── analyzer/
│   ├── base.py         # Abstract BaseAnalyzer interface
│   └── python_analyzer.py  # AST-based Python analyzer
├── estimators/
│   ├── energy.py       # Hotspot → kWh heuristics
│   └── carbon.py       # kWh → kg CO₂ via grid intensity
├── rules/
│   ├── loops.py        # Detect nested for/while loops
│   └── api_calls.py    # Detect uncached HTTP calls
├── core/
│   └── engine.py       # Orchestrates analyzer + estimators + suggestions
├── cli/
│   └── main.py         # Typer CLI (`carbon analyze` / `carbon serve`)
└── tests/
    └── test_analyzer.py
```

**Data flow:**

```
User code
  → PythonAnalyzer (AST rules)
      → list[Hotspot]
          → EnergyEstimator  → kWh
          → CarbonEstimator  → kg CO₂
          → SuggestionEngine → list[Suggestion]
              → AnalyzeResponse (JSON)
```

Adding a new rule is a single file drop into `rules/` and a one-line registration
in `analyzer/python_analyzer.py`.

---

## Quick Start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# or without editable install:
pip install -r requirements.txt
```

### 2. Run the API server

```bash
# Via CLI helper
carbon serve

# Or directly with uvicorn
uvicorn server.api:app --reload
```

The server starts on **http://127.0.0.1:8000**.  
Interactive docs: http://127.0.0.1:8000/docs

### 3. Analyze code via the API

```bash
curl -X POST http://localhost:8000/analyze_code \
  -H "Content-Type: application/json" \
  -d '{"code": "for i in range(100):\n    for j in range(100):\n        pass"}'
```

**Response:**

```json
{
  "emissions": {
    "estimated_co2_kg": 1.33e-9,
    "energy_kwh": 2.8e-9,
    "confidence": "low"
  },
  "hotspots": [
    {
      "line": 2,
      "type": "nested_loop",
      "description": "Nested loop detected (depth 2). This may result in O(n²) or worse complexity.",
      "severity": "high"
    }
  ],
  "suggestions": [
    {
      "hotspot_type": "nested_loop",
      "description": "Replace nested loops with a hash-map lookup",
      "guidance": "..."
    }
  ]
}
```

### 4. Analyze a file via the CLI

```bash
carbon analyze path/to/your_script.py
```

---

## Running Tests

```bash
pytest -v
```

---

## Extending Carbon MCP

### Add a new detection rule

1. Create `rules/my_rule.py` and implement a function:

   ```python
   def detect_my_pattern(tree: ast.AST) -> list[Hotspot]: ...
   ```

2. Register it in `analyzer/python_analyzer.py`:

   ```python
   from rules.my_rule import detect_my_pattern
   _RULES = [..., detect_my_pattern]
   ```

3. Optionally add a suggestion in `core/engine.py` under `_SUGGESTIONS`.

### Add a new language analyzer

1. Subclass `analyzer.base.BaseAnalyzer` and set `language = "js"`.
2. Register the instance in `core/engine._ANALYZERS`.

---

## Carbon Estimation Model

The model is intentionally heuristic and meant for directional guidance:

| Hotspot           | Energy / occurrence | Basis                              |
|-------------------|--------------------|------------------------------------|
| `nested_loop`     | 2.8 × 10⁻⁶ kWh    | 100×100 iterations on 100 W server |
| `repeated_api_call` | 3.6 × 10⁻⁷ kWh  | ~1 KB HTTPS round-trip             |

Grid intensity default: **0.475 kg CO₂ / kWh** (IEA 2022 world average).  
Override in `estimators/carbon.py` for region-specific accuracy.

---

## License

MIT
