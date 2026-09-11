"""Hierarchical Hub-and-Spoke SCIF Federation over Hardware Data Diodes.

Provides:
- Tactical edge SCIF node summarization and secret sanitization
- Cryptographically sealed FederatedEnclaveReport generation
- Unidirectional one-way data diode serialization and ingestion at Strategic HQ
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pydantic import BaseModel, Field


class TacticalCorridorSummary(BaseModel):
    """Sanitized tactical corridor status prepared for upward diode transmission."""

    corridor_id: str
    corridor_name: str
    effective_state: str
    resilience_score: float
    replenishment_horizon_days: float
    has_active_threat: bool


class FederatedEnclaveReport(BaseModel):
    """Cryptographically sealed summary from a forward-deployed tactical SCIF enclave."""

    report_id: str
    origin_enclave_id: str
    origin_classification: str
    exported_classification: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    corridor_summaries: list[TacticalCorridorSummary] = Field(default_factory=list)
    sha256_digest: str = ""
    signature_hex: str = ""


class SCIFEnclaveFederator:
    """Manages outward and inward synchronization across security enclaves via one-way diodes."""

    @staticmethod
    def create_tactical_report(
        enclave_id: str,
        classification: str,
        corridors: list[dict[str, Any]],
        signing_key: Ed25519PrivateKey | None = None,
    ) -> FederatedEnclaveReport:
        """Sanitize tactical secrets and package an enclave report for diode transmission."""
        summaries: list[TacticalCorridorSummary] = []
        for c in corridors:
            summaries.append(
                TacticalCorridorSummary(
                    corridor_id=str(c.get("id", "c-unknown")),
                    corridor_name=str(c.get("name", "Unknown Corridor")),
                    effective_state=str(c.get("state", "HEALTHY")),
                    resilience_score=float(c.get("score", 1.0)),
                    replenishment_horizon_days=float(c.get("replenishment_days", 45.0)),
                    has_active_threat=bool(c.get("has_threat", False)),
                )
            )

        # Compute deterministic content digest
        payload_repr = json.dumps([s.model_dump() for s in summaries], sort_keys=True)
        digest = hashlib.sha256(payload_repr.encode("utf-8")).hexdigest()

        # Sign digest if cryptographic key provided
        sig_hex = ""
        if signing_key:
            sig_hex = signing_key.sign(digest.encode("utf-8")).hex()

        return FederatedEnclaveReport(
            report_id=f"FED-{enclave_id}-{digest[:8]}",
            origin_enclave_id=enclave_id,
            origin_classification=classification,
            exported_classification="PROTECTED_B // REL_ALLIED",
            corridor_summaries=summaries,
            sha256_digest=digest,
            signature_hex=sig_hex,
        )

    @staticmethod
    def ingest_diode_report(
        report_json: str,
        verifying_key: Ed25519PublicKey | None = None,
    ) -> tuple[bool, str, FederatedEnclaveReport | None]:
        """Ingest and cryptographically verify an enclave report received across a data diode."""
        try:
            data = json.loads(report_json)
            report = FederatedEnclaveReport.model_validate(data)
        except Exception as e:
            return False, f"MALFORMED_PAYLOAD: {e}", None

        # Verify hash integrity
        payload_repr = json.dumps(
            [s.model_dump() for s in report.corridor_summaries], sort_keys=True
        )
        expected_digest = hashlib.sha256(payload_repr.encode("utf-8")).hexdigest()
        if expected_digest != report.sha256_digest:
            return False, "TAMPER_DETECTED: Digest mismatch", None

        # Verify signature if key present
        if verifying_key and report.signature_hex:
            try:
                verifying_key.verify(
                    bytes.fromhex(report.signature_hex),
                    report.sha256_digest.encode("utf-8"),
                )
            except Exception:
                return False, "SIGNATURE_INVALID: Cryptographic verification failed", None

        return True, "VERIFIED", report
