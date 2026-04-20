"""Core analysis engine.

Ties together the analyzer, estimators, and suggestion generator into a
single entry point consumed by both the API and the CLI.
"""
from __future__ import annotations

from analyzer.base import BaseAnalyzer
from analyzer.python_analyzer import PythonAnalyzer
from estimators.carbon import estimate_carbon
from estimators.energy import estimate_energy
from server.schemas import (
    AnalyzeResponse,
    Hotspot,
    Language,
    Suggestion,
)

# ---------------------------------------------------------------------------
# Suggestion catalogue
# ---------------------------------------------------------------------------

_SUGGESTIONS: dict[str, Suggestion] = {
    "nested_loop": Suggestion(
        hotspot_type="nested_loop",
        description="Replace nested loops with a hash-map lookup",
        guidance=(
            "Instead of iterating over a list inside another loop (O(n²)), "
            "build a dictionary / set from the inner collection first, then "
            "perform O(1) lookups in the outer loop.\n\n"
            "Example:\n"
            "  # Before\n"
            "  for a in list_a:\n"
            "      for b in list_b:\n"
            "          if a == b: ...\n\n"
            "  # After\n"
            "  lookup = set(list_b)\n"
            "  for a in list_a:\n"
            "      if a in lookup: ..."
        ),
    ),
    "repeated_api_call": Suggestion(
        hotspot_type="repeated_api_call",
        description="Cache API responses to avoid redundant network round-trips",
        guidance=(
            "Wrap HTTP calls with a simple in-process cache (e.g. "
            "``functools.lru_cache``, ``cachetools.TTLCache``, or a Redis "
            "layer for distributed setups).  Move the call outside any loops "
            "when the response does not change per iteration.\n\n"
            "Example:\n"
            "  from functools import lru_cache\n\n"
            "  @lru_cache(maxsize=128)\n"
            "  def fetch_data(url: str) -> dict:\n"
            "      return requests.get(url).json()"
        ),
    ),
}


# ---------------------------------------------------------------------------
# Analyzer registry
# ---------------------------------------------------------------------------

_ANALYZERS: dict[str, BaseAnalyzer] = {
    Language.python: PythonAnalyzer(),
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class Engine:
    """Orchestrates analysis, estimation, and suggestion generation."""

    def analyze(self, code: str, language: Language = Language.python) -> AnalyzeResponse:
        """Run the full pipeline and return a structured response.

        Args:
            code: Raw source code to analyze.
            language: Target programming language.

        Returns:
            :class:`~server.schemas.AnalyzeResponse` with emissions,
            hotspots, and suggestions.
        """
        analyzer = _ANALYZERS.get(language)
        if analyzer is None:
            raise ValueError(f"No analyzer registered for language '{language}'")

        hotspots: list[Hotspot] = analyzer.analyze(code)
        energy_kwh = estimate_energy(hotspots)
        emissions = estimate_carbon(energy_kwh)
        suggestions = self._build_suggestions(hotspots)

        return AnalyzeResponse(
            emissions=emissions,
            hotspots=hotspots,
            suggestions=suggestions,
        )

    @staticmethod
    def _build_suggestions(hotspots: list[Hotspot]) -> list[Suggestion]:
        """Return one suggestion per unique hotspot type that has a catalogue entry."""
        seen: set[str] = set()
        suggestions: list[Suggestion] = []
        for hotspot in hotspots:
            if hotspot.type not in seen and hotspot.type in _SUGGESTIONS:
                suggestions.append(_SUGGESTIONS[hotspot.type])
                seen.add(hotspot.type)
        return suggestions
