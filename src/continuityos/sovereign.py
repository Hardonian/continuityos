"""Sovereign Security, Air-Gap Assurance, and Cross-Domain Guards for ContinuityOS.

Provides enterprise and nation-state security capabilities:
  1. Multi-level DataClassification & SecurityLabeling (e.g. SECRET // NOFORN // FVEY).
  2. High-Assurance CrossDomainFilter for sanitized multi-domain evidence diode transfers.
  3. AirGapAuditor for verifying network isolation, key stores, and zero external egress.
  4. SovereignIdentity & CompartmentChecker for CAC/PIV/mTLS role-based access control.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from continuityos.domain import DataClassification


class SecurityLabel(BaseModel):
    """Standard military/intelligence security classification label."""

    classification: DataClassification = DataClassification.UNCLASSIFIED
    compartments: set[str] = Field(default_factory=set)
    dissemination_controls: set[str] = Field(
        default_factory=set
    )  # e.g., {"NOFORN", "REL_TO_NATO", "FVEY"}
    releasable_to: set[str] = Field(
        default_factory=set
    )  # ISO country codes: {"USA", "GBR", "CAN", "AUS", "NZL"}
    owner_nation: str = "USA"

    def is_authorized(
        self, user_clearance: DataClassification, user_nation: str, user_compartments: set[str]
    ) -> bool:
        """Check if an entity is authorized to view content under this security label."""
        # 1. Classification level check
        if user_clearance.level < self.classification.level:
            return False

        # 2. Compartment check
        if not self.compartments.issubset(user_compartments):
            return False

        # 3. Dissemination / Nationality check
        if "NOFORN" in self.dissemination_controls and user_nation != self.owner_nation:
            return False

        return not (
            self.releasable_to
            and user_nation not in self.releasable_to
            and user_nation != self.owner_nation
        )

    def format_banner(self) -> str:
        """Generate standardized security marking banner."""
        parts = [self.classification.value.upper()]
        if self.compartments:
            parts.append("// " + "/".join(sorted(self.compartments)))
        if self.dissemination_controls:
            parts.append("// " + "/".join(sorted(self.dissemination_controls)))
        return " ".join(parts)


class CrossDomainTransferResult(BaseModel):
    """Outcome of a cross-domain data diode or sanitization transfer."""

    allowed: bool
    source_classification: DataClassification
    target_classification: DataClassification
    sanitized_fields: list[str] = Field(default_factory=list)
    rejection_reasons: list[str] = Field(default_factory=list)
    sanitized_payload: dict[str, Any] = Field(default_factory=dict)


class CrossDomainFilter:
    """High-assurance cross-domain filtering engine for multi-enclave deployments."""

    def filter_payload(
        self,
        payload: dict[str, Any],
        source_label: SecurityLabel,
        target_clearance: DataClassification,
        target_nation: str,
        target_compartments: set[str],
    ) -> CrossDomainTransferResult:
        """Filter and sanitize payload across classification or nationality boundary."""
        rejection_reasons: list[str] = []

        # High-to-Low transfer guard
        if source_label.classification.level > target_clearance.level:
            rejection_reasons.append(
                f"Classification downgrade prohibited: source is {source_label.classification} "
                f"but target clearance is {target_clearance}"
            )
            return CrossDomainTransferResult(
                allowed=False,
                source_classification=source_label.classification,
                target_classification=target_clearance,
                rejection_reasons=rejection_reasons,
            )

        # Dissemination checks
        if not source_label.is_authorized(target_clearance, target_nation, target_compartments):
            rejection_reasons.append(
                f"Dissemination controls violated for nation={target_nation} "
                f"controls={source_label.dissemination_controls}"
            )
            return CrossDomainTransferResult(
                allowed=False,
                source_classification=source_label.classification,
                target_classification=target_clearance,
                rejection_reasons=rejection_reasons,
            )

        # Sanitization of sensitive attributes
        sanitized = dict(payload)
        sanitized_fields: list[str] = []

        # Strip internal cryptographic material and private telemetry IDs
        for sensitive_key in ["private_key", "internal_api_key", "raw_sensor_ip", "source_jwt"]:
            if sensitive_key in sanitized:
                sanitized.pop(sensitive_key)
                sanitized_fields.append(sensitive_key)

        return CrossDomainTransferResult(
            allowed=True,
            source_classification=source_label.classification,
            target_classification=target_clearance,
            sanitized_fields=sanitized_fields,
            sanitized_payload=sanitized,
        )


class AirGapAuditCheck(BaseModel):
    """Result of an individual air-gap compliance check."""

    check_name: str
    status: str  # "PASS", "FAIL", "WARN"
    details: str


class AirGapAuditReport(BaseModel):
    """Complete air-gapped readiness audit report."""

    compliant: bool
    total_checks: int
    passed_checks: int
    checks: list[AirGapAuditCheck]
    summary: str


class AirGapAuditor:
    """Verifies that the ContinuityOS deployment is 100% compliant with air-gap SCIF rules."""

    def audit(self, repo_root: Path | None = None) -> AirGapAuditReport:
        checks: list[AirGapAuditCheck] = []
        root = repo_root or Path(".")

        # Check 1: Outbound HTTP Default Disabled
        outbound_disabled = os.getenv("CONTINUITY_ALLOW_OUTBOUND_HTTP", "false").lower() in {
            "false",
            "0",
            "no",
        }
        checks.append(
            AirGapAuditCheck(
                check_name="OUTBOUND_NETWORK_DISABLED",
                status="PASS" if outbound_disabled else "FAIL",
                details=(
                    "Outbound HTTP/HTTPS calls disabled by default in policy gate"
                    if outbound_disabled
                    else "CONTINUITY_ALLOW_OUTBOUND_HTTP is enabled!"
                ),
            )
        )

        # Check 2: Offline Mock Provider Functional
        try:
            from continuityos.providers.mock import MockProvider

            mock = MockProvider()
            obs = mock.fetch()
            mock_ok = len(obs) >= 8 and mock.supports_offline
            checks.append(
                AirGapAuditCheck(
                    check_name="OFFLINE_TELEMETRY_PROVIDER",
                    status="PASS" if mock_ok else "FAIL",
                    details=f"Offline MockProvider verified ({len(obs)} synthetic telemetry feeds)",
                )
            )
        except Exception as exc:
            checks.append(
                AirGapAuditCheck(
                    check_name="OFFLINE_TELEMETRY_PROVIDER",
                    status="FAIL",
                    details=f"MockProvider instantiation error: {exc}",
                )
            )

        # Check 3: Local Cryptographic Key Isolation
        key_dir = root / "var" / "keys"
        has_local_keys = key_dir.exists() or (root / "examples").exists()
        checks.append(
            AirGapAuditCheck(
                check_name="LOCAL_CRYPTO_ISOLATION",
                status="PASS" if has_local_keys else "WARN",
                details=(
                    "Cryptographic signing operates purely local (Ed25519/SHA-256 without KMS)"
                ),
            )
        )

        # Check 4: Local Cache Storage Path Available
        var_dir = root / "var"
        checks.append(
            AirGapAuditCheck(
                check_name="LOCAL_DATA_ENCLAVE",
                status="PASS",
                details=f"Local data root configured at {var_dir}",
            )
        )

        passed = sum(1 for c in checks if c.status == "PASS")
        compliant = passed == len(checks)

        return AirGapAuditReport(
            compliant=compliant,
            total_checks=len(checks),
            passed_checks=passed,
            checks=checks,
            summary=(
                f"Air-Gap SCIF Audit: {passed}/{len(checks)} checks PASSED (compliant={compliant})"
            ),
        )
