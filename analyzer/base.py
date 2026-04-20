"""Abstract base class for all language analyzers."""
from __future__ import annotations

from abc import ABC, abstractmethod

from server.schemas import Hotspot


class BaseAnalyzer(ABC):
    """Interface every language analyzer must implement."""

    #: Human-readable language identifier, e.g. "python"
    language: str = ""

    @abstractmethod
    def analyze(self, code: str) -> list[Hotspot]:
        """Parse *code* and return a list of detected hotspots."""
        ...
