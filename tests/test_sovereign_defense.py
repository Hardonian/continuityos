"""Comprehensive test suite for ContinuityOS Sovereign Defense & Nation-State Security Suite.

Tests:
  1. SecurityLabel and Classification enforcement (UNCLASSIFIED to COSMIC_TOP_SECRET).
  2. CrossDomainFilter & Diode Sanitization.
  3. AirGapAuditor for SCIF deployments and zero external telemetry egress.
  4. Defense Readiness (DRRS) & NATO C-Level Capability Rating Engine.
  5. Mil-Std-2525D / NATO APP-6D Common Operating Picture (COP) Symbology.
  6. Sovereign CLI subcommands.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from continuityos.cop import export_cop_feature, export_cop_feature_collection
from continuityos.domain import (
    CorridorAssessment,
    CorridorFactor,
    CorridorState,
    DataClassification,
    FactorAssessment,
)
from continuityos.readiness import CLevelRating, ReadinessEngine
from continuityos.sovereign import (
    AirGapAuditor,
    CrossDomainFilter,
    SecurityLabel,
)


class TestSecurityLabelingAndClearance:
    """Test multi-level security labeling and dissemination controls."""

    def test_classification_hierarchy_levels(self) -> None:
        assert DataClassification.UNCLASSIFIED.level == 0
        assert DataClassification.RESTRICTED.level == 2
        assert DataClassification.CONFIDENTIAL.level == 3
        assert DataClassification.SECRET.level == 4
        assert DataClassification.TOP_SECRET.level == 5
        assert DataClassification.COSMIC_TOP_SECRET.level == 6

    def test_security_label_authorization_matrix(self) -> None:
        secret_noforn = SecurityLabel(
            classification=DataClassification.SECRET,
            dissemination_controls={"NOFORN"},
            owner_nation="USA",
        )

        # US Citizen with SECRET clearance -> Authorized
        assert secret_noforn.is_authorized(DataClassification.SECRET, "USA", set()) is True
        assert secret_noforn.is_authorized(DataClassification.TOP_SECRET, "USA", set()) is True

        # US Citizen with CONFIDENTIAL clearance -> Denied
        assert secret_noforn.is_authorized(DataClassification.CONFIDENTIAL, "USA", set()) is False

        # Foreign national with SECRET clearance -> Denied due to NOFORN
        assert secret_noforn.is_authorized(DataClassification.SECRET, "GBR", set()) is False

    def test_releasable_to_fvey_allies(self) -> None:
        fvey_label = SecurityLabel(
            classification=DataClassification.SECRET,
            dissemination_controls={"REL_TO_FVEY"},
            releasable_to={"USA", "GBR", "CAN", "AUS", "NZL"},
            owner_nation="USA",
        )
        assert fvey_label.is_authorized(DataClassification.SECRET, "GBR", set()) is True
        assert fvey_label.is_authorized(DataClassification.SECRET, "AUS", set()) is True
        assert fvey_label.is_authorized(DataClassification.SECRET, "FRA", set()) is False

    def test_compartment_enforcement(self) -> None:
        special_access = SecurityLabel(
            classification=DataClassification.TOP_SECRET,
            compartments={"SI", "TK", "G"},
            owner_nation="USA",
        )
        # Missing TK compartment -> Denied
        assert (
            special_access.is_authorized(DataClassification.TOP_SECRET, "USA", {"SI", "G"}) is False
        )

        # Has all compartments -> Authorized
        assert (
            special_access.is_authorized(
                DataClassification.TOP_SECRET, "USA", {"SI", "TK", "G", "HCS"}
            )
            is True
        )


class TestCrossDomainFilterAndSanitization:
    """Test data diode filtering across security enclaves."""

    def test_cross_domain_downgrade_prevention(self) -> None:
        filter_engine = CrossDomainFilter()
        source_label = SecurityLabel(classification=DataClassification.SECRET)

        payload = {"corridor_id": "kara-sea", "continuity_score": 0.85}
        result = filter_engine.filter_payload(
            payload,
            source_label=source_label,
            target_clearance=DataClassification.UNCLASSIFIED,
            target_nation="USA",
            target_compartments=set(),
        )
        assert result.allowed is False
        assert any("downgrade prohibited" in r for r in result.rejection_reasons)

    def test_cross_domain_sensitive_key_sanitization(self) -> None:
        filter_engine = CrossDomainFilter()
        source_label = SecurityLabel(classification=DataClassification.RESTRICTED)

        payload = {
            "corridor_id": "rotterdam-harbor",
            "capacity": 0.92,
            "private_key": "-----BEGIN PRIVATE KEY-----",
            "internal_api_key": "sec_12345",
            "raw_sensor_ip": "10.0.4.15",
        }
        result = filter_engine.filter_payload(
            payload,
            source_label=source_label,
            target_clearance=DataClassification.RESTRICTED,
            target_nation="USA",
            target_compartments=set(),
        )
        assert result.allowed is True
        assert "private_key" not in result.sanitized_payload
        assert "internal_api_key" not in result.sanitized_payload
        assert "raw_sensor_ip" not in result.sanitized_payload
        assert result.sanitized_payload["capacity"] == 0.92
        assert len(result.sanitized_fields) == 3


class TestAirGapAuditor:
    """Test sovereign air-gap compliance auditing."""

    def test_air_gap_audit_execution(self) -> None:
        auditor = AirGapAuditor()
        report = auditor.audit(Path("."))
        assert report.total_checks >= 4
        assert report.passed_checks >= 3
        assert any(c.check_name == "OFFLINE_TELEMETRY_PROVIDER" for c in report.checks)


class TestReadinessEngine:
    """Test Defense Readiness (DRRS) & C-Level Capability Rating."""

    def test_c1_fully_mission_capable(self) -> None:
        engine = ReadinessEngine()
        assessment = engine.evaluate_readiness(
            "theatre-nordic-1",
            overall_continuity=0.98,
            inventory_reserve_days=45.0,
            corridor_state=CorridorState.OPEN,
        )
        assert assessment.c_rating == CLevelRating.C1_FULLY_MISSION_CAPABLE
        assert assessment.inventory_readiness_score == 1.0
        assert len(assessment.mission_limiting_factors) == 0

    def test_c3_marginally_capable_on_degraded_comms(self) -> None:
        engine = ReadinessEngine()
        assessment = engine.evaluate_readiness(
            "theatre-polar-2",
            overall_continuity=0.82,
            inventory_reserve_days=25.0,
            corridor_state=CorridorState.OPEN_BUT_COMMUNICATIONS_DEGRADED,
        )
        assert assessment.c_rating == CLevelRating.C3_MARGINALLY_CAPABLE
        assert any(f.factor_id == "CORRIDOR_DEGRADED" for f in assessment.mission_limiting_factors)

    def test_c4_not_capable_on_corridor_closure_or_fuel_drain(self) -> None:
        engine = ReadinessEngine()
        assessment = engine.evaluate_readiness(
            "theatre-indo-pac-3",
            overall_continuity=0.40,
            inventory_reserve_days=4.0,
            corridor_state=CorridorState.FUNCTIONALLY_CLOSED,
        )
        assert assessment.c_rating == CLevelRating.C4_NOT_MISSION_CAPABLE
        assert len(assessment.mission_limiting_factors) >= 2


class TestMilitarySymbologyAndCOPExport:
    """Test Mil-Std-2525D / NATO APP-6D Common Operating Picture exports."""

    def test_export_cop_geojson_feature(self) -> None:
        assessment = CorridorAssessment(
            assessment_id=uuid4(),
            corridor_id="sector-arctic-1",
            overall_risk=0.75,
            confidence=0.90,
            state=CorridorState.OPEN_BUT_NAVIGATION_UNTRUSTED,
            factors=[
                FactorAssessment(
                    factor=CorridorFactor.CYBER,
                    risk=0.80,
                    confidence=0.90,
                    evidence_ids=[],
                    rationale="GNSS Spoofing detected across sector",
                )
            ],
            missing_required_metrics=[],
            caveats=["PNT untrusted"],
        )
        feat = export_cop_feature("sector-arctic-1", assessment, security_banner="SECRET // NOFORN")
        assert feat["type"] == "Feature"
        assert feat["id"] == "sector-arctic-1"
        assert feat["properties"]["mil_std_2525_sidc"] == "10043000001206000000"
        assert feat["properties"]["security_classification_banner"] == "SECRET // NOFORN"
        assert feat["properties"]["operational_condition"] == "Navigation Denied"

        collection = export_cop_feature_collection([feat])
        assert collection["type"] == "FeatureCollection"
        assert len(collection["features"]) == 1
        assert "MIL-STD-2525D" in collection["properties"]["symbology_standard"]


class TestSovereignCLICommands:
    """Test sovereign CLI integration via click/argparse."""

    def test_cli_sovereign_audit_execution(self, tmp_path: Path) -> None:
        from continuityos.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["sovereign-audit", "--repo-dir", str(tmp_path)])
        assert args.command == "sovereign-audit"

    def test_cli_readiness_command_parsing(self, tmp_path: Path) -> None:
        from continuityos.cli import build_parser

        spec_file = tmp_path / "readiness.json"
        spec_file.write_text(
            json.dumps(
                {
                    "theater_id": "theater-arctic",
                    "overall_continuity": 0.88,
                    "inventory_reserve_days": 18.0,
                    "corridor_state": "open_degraded",
                }
            )
        )
        parser = build_parser()
        args = parser.parse_args(["readiness", str(spec_file)])
        assert args.command == "readiness"
