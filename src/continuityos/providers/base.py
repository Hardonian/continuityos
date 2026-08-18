"""Provider SDK base protocol.

Providers are external data sources that fetch, normalize, validate,
and return observations. They decouple ContinuityOS from any specific
data source or API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from continuityos.domain import Observation


class Provider(ABC):
    """Abstract base class for ContinuityOS data providers."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable name for this provider."""

    @abstractmethod
    def fetch(self, *, as_of: datetime | None = None) -> list[Observation]:
        """Fetch and return normalized observations.

        Implementations must:
        1. Fetch raw data from the external source
        2. Normalize values into ContinuityOS domain metrics
        3. Validate observations against domain constraints
        4. Attach timestamps and provenance
        5. Return typed Observation instances
        """

    @abstractmethod
    def validate(self, observations: list[Observation]) -> list[str]:
        """Validate observations, returning a list of error messages."""

    @property
    def supports_offline(self) -> bool:
        """Whether this provider can operate without network access."""
        return False
