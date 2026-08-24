"""Test suite for Strategic War-Gaming, Game-Theoretic Disruption, and Critical Minerals."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.service import create_app
from continuityos.wargame import (
    CANADIAN_CRITICAL_MINERALS,
    DisruptionScenarioType,
    WargameSimulator,
)


class TestWargameSimulator:
    """Test game-theoretic wargame and critical mineral depletion modeling."""

    def test_wargame_simulation_maritime_blockade(self) -> None:
        simulator = WargameSimulator()
        report = simulator.run_simulation(
            scenario_type=DisruptionScenarioType.MARITIME_BLOCKADE,
            corridor_id="ST-LAWRENCE-SEAWAY",
            horizons_days=[30, 60, 90, 180],
            adversary_pressure_level=0.8,
            domestic_reserves_cushion=0.4,
        )

        assert len(report.stages) == 4
        assert report.target_corridor_id == "ST-LAWRENCE-SEAWAY"
        assert len(report.strategic_options) >= 3
        assert report.critical_failure_day is not None
        assert report.stages[0].nato_readiness_score > report.stages[3].nato_readiness_score

    def test_critical_minerals_database(self) -> None:
        assert "NICKEL" in CANADIAN_CRITICAL_MINERALS
        assert "LITHIUM" in CANADIAN_CRITICAL_MINERALS
        assert "RARE_EARTHS" in CANADIAN_CRITICAL_MINERALS

        nickel = CANADIAN_CRITICAL_MINERALS["NICKEL"]
        assert nickel.domestic_refining_capacity_percent > 50.0
        assert nickel.stockpile_days_remaining_baseline >= 90


class TestWargameAPI:
    """Test wargame REST endpoints."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_wargame_simulate_endpoint(self, client: TestClient) -> None:
        payload = {
            "scenario_type": "maritime_blockade",
            "corridor_id": "TEST-SEAWAY",
            "horizons_days": [30, 60],
            "adversary_pressure_level": 0.7,
        }
        resp = client.post("/v1/wargame/simulate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["stages"]) == 2
        assert "strategic_options" in data

    def test_critical_minerals_endpoint(self, client: TestClient) -> None:
        resp = client.get("/v1/wargame/critical-minerals")
        assert resp.status_code == 200
        data = resp.json()
        assert "NICKEL" in data["critical_minerals"]
