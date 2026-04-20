"""Carbon intensity estimator.

Converts an energy estimate (kWh) into a CO₂ equivalent (kg).

We use the global average carbon intensity of the electricity grid as a
baseline:  ~0.475 kg CO₂ / kWh  (IEA 2022 world average).

Override ``CARBON_INTENSITY_KG_PER_KWH`` with a region-specific value for
more accurate results (e.g. 0.233 for the EU, 0.386 for the US average).
"""
from __future__ import annotations

from server.schemas import Confidence, Emissions

# Default: IEA world-average grid carbon intensity (kg CO₂ / kWh)
CARBON_INTENSITY_KG_PER_KWH: float = 0.475


def estimate_carbon(
    energy_kwh: float,
    *,
    intensity: float = CARBON_INTENSITY_KG_PER_KWH,
) -> Emissions:
    """Convert *energy_kwh* to an :class:`~server.schemas.Emissions` object.

    Args:
        energy_kwh: Estimated energy in kilo-watt hours.
        intensity: Grid carbon intensity in kg CO₂ / kWh.

    Returns:
        An :class:`Emissions` instance with confidence always set to
        ``"low"`` because the underlying hotspot counts are heuristic.
    """
    co2_kg = energy_kwh * intensity
    return Emissions(
        estimated_co2_kg=round(co2_kg, 10),
        energy_kwh=round(energy_kwh, 10),
        confidence=Confidence.low,
    )
