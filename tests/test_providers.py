"""Tests for Provider SDK and MockProvider implementation."""

from __future__ import annotations

from datetime import UTC, datetime

from continuityos.providers.base import Provider
from continuityos.providers.mock import MockProvider


class TestProviders:
    def test_mock_provider_scenarios(self) -> None:
        normal = MockProvider(scenario="normal")
        assert issubclass(MockProvider, Provider)
        assert normal.supports_offline is True
        assert normal.provider_id == "mock-provider"

        obs_normal = normal.fetch()
        assert len(obs_normal) >= 8
        assert normal.validate(obs_normal) == []

        degraded = MockProvider(scenario="degraded")
        obs_degraded = degraded.fetch()
        assert len(obs_degraded) >= 8

        disrupted = MockProvider(scenario="disrupted")
        obs_disrupted = disrupted.fetch()
        assert len(obs_disrupted) >= 8

    def test_mock_provider_with_timestamp(self) -> None:
        provider = MockProvider()
        as_of = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        obs = provider.fetch(as_of=as_of)
        assert all(o.observed_at == as_of for o in obs)
