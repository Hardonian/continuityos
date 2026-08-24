"""Test suite for PBMMComplianceValidator, Canadian corridor APIs, and RFP endpoints."""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from continuityos.service import create_app
from continuityos.sovereign import PBMMComplianceValidator


class TestPBMMComplianceValidator:
    """Test automated CCCS ITSG-33 Protected B compliance checking."""

    def test_canadian_residency_validation_pass(self) -> None:
        validator = PBMMComplianceValidator()
        report = validator.validate_deployment(
            region="ca-central-1",
            encryption_at_rest_cmk=True,
            tls_version="1.3",
            airgap_capable=True,
            immutable_evidence_chain=True,
            rbac_clearance_filtering=True,
        )

        assert report.is_compliant is True
        assert report.canadian_sovereignty_enforced is True
        assert report.satisfied_controls_count == 6
        assert len(report.controls) == 6

    def test_foreign_residency_validation_fail(self) -> None:
        validator = PBMMComplianceValidator()
        report = validator.validate_deployment(
            region="us-east-1",  # Non-Canadian region
            encryption_at_rest_cmk=True,
        )

        assert report.is_compliant is False
        assert report.canadian_sovereignty_enforced is False


class TestCanadianAndSupplyChainAPIEndpoints:
    """Test new REST API endpoints on FastAPI app."""

    @pytest.fixture
    def client(self) -> TestClient:
        app = create_app()
        return TestClient(app)

    def test_list_canadian_corridors_endpoint(self, client: TestClient) -> None:
        resp = client.get("/v1/canadian/corridors")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 4
        assert data["sovereign_region"] == "CANADA"

    def test_rfp_package_summary_endpoint(self, client: TestClient) -> None:
        resp = client.get("/v1/rfp/package-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "ITSG-33" in data["security_certification_profile"]
        assert "99.99%" in data["sla_and_recovery_objectives"]["availability_sla"]

    def test_supply_chain_economic_impact_endpoint(self, client: TestClient) -> None:
        payload = {
            "disruption_duration_days": 14,
            "daily_inventory_value_cad": 6000000.0,
            "vessels_delayed_count": 2,
            "demurrage_rate_per_vessel_daily_cad": 25000.0,
            "production_line_daily_burn_cad": 150000.0,
        }
        resp = client.post("/v1/supply-chain/economic-impact", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_estimated_loss_cad"] > 2_000_000.0
        assert data["total_demurrage_cost"] == 700_000.0

    def test_supply_chain_reroute_endpoint(self, client: TestClient) -> None:
        payload = {
            "corridor_id": "TEST-CORRIDOR",
            "origin": "Vancouver",
            "destination": "Toronto",
            "distance_km": 4350.0,
            "time_critical": False,
        }
        resp = client.post("/v1/supply-chain/reroute", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_options_evaluated"] >= 4
        assert "recommended_mode" in data

    def test_pbmm_audit_endpoint(self, client: TestClient) -> None:
        payload = {
            "region": "ca-central-1",
            "encryption_at_rest_cmk": True,
            "tls_version": "1.3",
        }
        resp = client.post("/v1/sovereign/pbmm-audit", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_compliant"] is True
        assert data["data_residency_region"] == "ca-central-1"
