"""Mock provider for offline operation and testing.

Provides synthetic but realistic observations for all major metric types.
Allows the entire ContinuityOS system to work without external data sources.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from uuid import uuid4

from continuityos.domain import (
    AssertionClass,
    MetricName,
    Observation,
    Provenance,
    SourceTrust,
)
from continuityos.providers.base import Provider


class MockProvider(Provider):
    """Mock provider that generates synthetic observations for testing."""

    def __init__(self, *, scenario: str = "normal") -> None:
        self._scenario = scenario

    @property
    def provider_id(self) -> str:
        return "mock-provider"

    @property
    def provider_name(self) -> str:
        return "ContinuityOS Mock Provider"

    @property
    def supports_offline(self) -> bool:
        return True

    def fetch(self, *, as_of: datetime | None = None) -> list[Observation]:
        """Generate synthetic observations based on scenario."""
        now = as_of or datetime.now(UTC)
        scenarios = {
            "normal": self._normal_observations,
            "degraded": self._degraded_observations,
            "disrupted": self._disrupted_observations,
        }
        generator = scenarios.get(self._scenario, self._normal_observations)
        return generator(now)

    def validate(self, observations: list[Observation]) -> list[str]:
        errors: list[str] = []
        for obs in observations:
            if obs.source_id != "mock-provider":
                errors.append(f"unexpected source: {obs.source_id}")
        return errors

    def _make_observation(
        self,
        now: datetime,
        metric: MetricName,
        value: float,
        unit: str,
        source_trust: SourceTrust,
        assertion_class: AssertionClass,
        confidence: float = 0.9,
    ) -> Observation:
        return Observation(
            observation_id=uuid4(),
            source_id="mock-provider",
            source_trust=source_trust,
            assertion_class=assertion_class,
            metric=metric,
            value=value,
            unit=unit,
            observed_at=now,
            confidence=confidence,
            provenance=Provenance(
                uri="mock://synthetic",
                content_sha256=hashlib.sha256(
                    f"{metric}:{value}:{now.isoformat()}".encode()
                ).hexdigest(),
                licence="synthetic-data",
            ),
            metadata={"synthetic": True, "scenario": self._scenario},
        )

    def _normal_observations(self, now: datetime) -> list[Observation]:
        return [
            self._make_observation(
                now,
                MetricName.SEA_ICE_CONCENTRATION,
                35.0,
                "percent",
                SourceTrust.AUTHORITATIVE_PUBLIC,
                AssertionClass.ICE,
            ),
            self._make_observation(
                now,
                MetricName.WIND_SEVERITY,
                0.3,
                "ratio",
                SourceTrust.AUTHORITATIVE_PUBLIC,
                AssertionClass.WEATHER,
            ),
            self._make_observation(
                now,
                MetricName.PORT_AVAILABILITY,
                0.85,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_AVAILABILITY,
            ),
            self._make_observation(
                now,
                MetricName.SATCOM_AVAILABILITY,
                0.95,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_AVAILABILITY,
            ),
            self._make_observation(
                now,
                MetricName.CYBER_CONTROL_HEALTH,
                0.92,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.CYBER_HEALTH,
            ),
            self._make_observation(
                now,
                MetricName.DATA_INTEGRITY,
                0.88,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.CYBER_HEALTH,
            ),
            self._make_observation(
                now,
                MetricName.INSURANCE_AVAILABILITY,
                0.78,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.INSURANCE_ACCESS,
            ),
            self._make_observation(
                now,
                MetricName.ESCORT_CAPACITY,
                0.7,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_CAPACITY,
            ),
            self._make_observation(
                now,
                MetricName.INVENTORY_DAYS,
                25.0,
                "days",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_CAPACITY,
            ),
        ]

    def _degraded_observations(self, now: datetime) -> list[Observation]:
        return [
            self._make_observation(
                now,
                MetricName.SEA_ICE_CONCENTRATION,
                65.0,
                "percent",
                SourceTrust.AUTHORITATIVE_PUBLIC,
                AssertionClass.ICE,
            ),
            self._make_observation(
                now,
                MetricName.WIND_SEVERITY,
                0.6,
                "ratio",
                SourceTrust.AUTHORITATIVE_PUBLIC,
                AssertionClass.WEATHER,
            ),
            self._make_observation(
                now,
                MetricName.PORT_AVAILABILITY,
                0.55,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_AVAILABILITY,
            ),
            self._make_observation(
                now,
                MetricName.SATCOM_AVAILABILITY,
                0.4,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_AVAILABILITY,
            ),
            self._make_observation(
                now,
                MetricName.CYBER_CONTROL_HEALTH,
                0.6,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.CYBER_HEALTH,
            ),
            self._make_observation(
                now,
                MetricName.DATA_INTEGRITY,
                0.55,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.CYBER_HEALTH,
            ),
            self._make_observation(
                now,
                MetricName.INSURANCE_AVAILABILITY,
                0.3,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.INSURANCE_ACCESS,
            ),
            self._make_observation(
                now,
                MetricName.ESCORT_CAPACITY,
                0.3,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_CAPACITY,
                0.7,
            ),
            self._make_observation(
                now,
                MetricName.INVENTORY_DAYS,
                12.0,
                "days",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_CAPACITY,
            ),
        ]

    def _disrupted_observations(self, now: datetime) -> list[Observation]:
        return [
            self._make_observation(
                now,
                MetricName.SEA_ICE_CONCENTRATION,
                85.0,
                "percent",
                SourceTrust.AUTHORITATIVE_PUBLIC,
                AssertionClass.ICE,
            ),
            self._make_observation(
                now,
                MetricName.WIND_SEVERITY,
                0.85,
                "ratio",
                SourceTrust.AUTHORITATIVE_PUBLIC,
                AssertionClass.WEATHER,
            ),
            self._make_observation(
                now,
                MetricName.PORT_AVAILABILITY,
                0.1,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_AVAILABILITY,
            ),
            self._make_observation(
                now,
                MetricName.SATCOM_AVAILABILITY,
                0.15,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_AVAILABILITY,
            ),
            self._make_observation(
                now,
                MetricName.CYBER_CONTROL_HEALTH,
                0.3,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.CYBER_HEALTH,
            ),
            self._make_observation(
                now,
                MetricName.DATA_INTEGRITY,
                0.25,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.CYBER_HEALTH,
            ),
            self._make_observation(
                now,
                MetricName.INSURANCE_AVAILABILITY,
                0.05,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.INSURANCE_ACCESS,
            ),
            self._make_observation(
                now,
                MetricName.ESCORT_CAPACITY,
                0.1,
                "ratio",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_CAPACITY,
                0.5,
            ),
            self._make_observation(
                now,
                MetricName.INVENTORY_DAYS,
                5.0,
                "days",
                SourceTrust.AUTHENTICATED_OPERATOR,
                AssertionClass.LIVE_CAPACITY,
            ),
        ]
