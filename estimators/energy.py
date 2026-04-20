"""Heuristic energy estimator.

Maps hotspot types and counts to an estimated energy consumption (kWh).
These values are intentionally coarse — the goal is directional guidance,
not scientific precision.

Reference ballpark figures used:
* A single CPU-intensive nested-loop execution (10 000 iterations²) on an
  average server (100 W TDP, ~10% utilisation) ≈ 2.8 × 10⁻⁶ kWh.
* A single HTTPS round-trip (≈ 1 KB payload) ≈ 3.6 × 10⁻⁷ kWh.

We scale linearly with the number of hotspots as a rough proxy for "how
often this runs in a typical minute of execution".
"""
from __future__ import annotations

from server.schemas import Hotspot

# Energy per single occurrence of each hotspot type (kWh)
_ENERGY_PER_OCCURRENCE: dict[str, float] = {
    "nested_loop": 2.8e-6,
    "repeated_api_call": 3.6e-7,
    "syntax_error": 0.0,
}

_DEFAULT_ENERGY: float = 1.0e-7  # fallback for unknown types


def estimate_energy(hotspots: list[Hotspot]) -> float:
    """Return total estimated energy in kWh for the supplied hotspots."""
    total = 0.0
    for hotspot in hotspots:
        total += _ENERGY_PER_OCCURRENCE.get(hotspot.type, _DEFAULT_ENERGY)
    return total
