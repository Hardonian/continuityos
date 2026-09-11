"""Tests for ContinuityOS Government Adoption & Procurement Suite.

Verifies:
- CycloneDX v1.5 and SPDX v2.3 Software Bill of Materials (SBOM) generation
- CCCS ITSG-33 / PBMM Compliance Matrix compilation
- Canadian Data Residency & ITB Value Proposition attestation
- NATO C-Level Defense Readiness attestation
- Cryptographic SHA-256 Merkle root sealing & Ed25519 signature verification
- Command-line interface integration (sbom, government-pack, verify-compliance)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from continuityos.cli import build_parser
from continuityos.procurement import (
    ITSG33_CONTROLS,
    compile_government_procurement_pack,
    verify_procurement_pack,
)
from continuityos.sbom import (
    RUNTIME_DEPENDENCIES,
    generate_cyclonedx_sbom,
    generate_spdx_sbom,
    verify_sbom_integrity,
)


def test_cyclonedx_sbom_generation() -> None:
    """Verify that CycloneDX SBOM adheres to standard v1.5 JSON specifications."""
    sbom = generate_cyclonedx_sbom()
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"
    assert "serialNumber" in sbom
    assert "metadata" in sbom
    assert sbom["metadata"]["component"]["name"] == "continuityos"
    assert sbom["metadata"]["component"]["properties"][0]["name"] == "sovereign:classification"
    assert sbom["metadata"]["component"]["properties"][0]["value"] == "PROTECTED_B"

    # Verify components
    components = sbom["components"]
    assert len(components) >= len(RUNTIME_DEPENDENCIES)

    # Verify that Python runtime dependencies exist
    dep_names = {c["name"] for c in components if c["type"] == "library"}
    for req in ("pydantic", "cryptography", "fastapi", "uvicorn", "pyyaml"):
        assert req in dep_names

    # Verify that internal files contain SHA-256 digests
    files = [c for c in components if c["type"] == "file"]
    assert len(files) > 10
    for f in files:
        assert len(f["hashes"]) >= 1
        assert f["hashes"][0]["alg"] == "SHA-256"
        assert len(f["hashes"][0]["content"]) == 64

    assert verify_sbom_integrity(sbom) is True


def test_spdx_sbom_generation() -> None:
    """Verify that SPDX SBOM adheres to standard v2.3 JSON specifications."""
    spdx = generate_spdx_sbom()
    assert spdx["spdxVersion"] == "SPDX-2.3"
    assert spdx["dataLicense"] == "CC0-1.0"
    assert spdx["SPDXID"] == "SPDXRef-DOCUMENT"
    assert "creationInfo" in spdx
    assert len(spdx["packages"]) >= len(RUNTIME_DEPENDENCIES) + 1
    assert len(spdx["relationships"]) >= len(RUNTIME_DEPENDENCIES)

    assert verify_sbom_integrity(spdx) is True


def test_government_procurement_pack_compilation_and_signature(tmp_path: Path) -> None:
    """Verify that compile_government_procurement_pack creates and cryptographically seals all artifacts."""
    out_dir = tmp_path / "procurement-pack"
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    manifest = compile_government_procurement_pack(out_dir, private_key=private_key)

    assert manifest["package"] == "ContinuityOS Government Adoption & Procurement Suite"
    assert manifest["verified"] is True
    assert manifest["ed25519_signature"] is not None
    assert len(manifest["merkle_root_sha256"]) == 64

    # Verify files created on disk
    expected_files = [
        "ITSG33_PBMM_COMPLIANCE_MATRIX.json",
        "CANADIAN_DATA_RESIDENCY_ATTESTATION.json",
        "NATO_DEFENSE_READINESS_ATTESTATION.json",
        "SBOM_CYCLONEDX.json",
        "SBOM_SPDX.json",
        "STATEMENT_OF_WORK_AND_ATO.md",
        "SEALED_EVIDENCE_DIGEST.json",
    ]
    for fn in expected_files:
        assert (out_dir / fn).is_file()

    # Verify ITSG-33 matrix content
    matrix_data = json.loads(
        (out_dir / "ITSG33_PBMM_COMPLIANCE_MATRIX.json").read_text(encoding="utf-8")
    )
    assert matrix_data["overall_status"] == "FULLY_COMPLIANT"
    assert len(matrix_data["controls"]) == len(ITSG33_CONTROLS)

    # Verify cryptographic verification helper
    assert verify_procurement_pack(out_dir, public_key=public_key) is True

    # Tampering test: modify one character in one file
    tampered_file = out_dir / "STATEMENT_OF_WORK_AND_ATO.md"
    tampered_file.write_text("TAMPERED CONTENT", encoding="utf-8")
    assert verify_procurement_pack(out_dir, public_key=public_key) is False


def test_cli_government_pack(tmp_path: Path) -> None:
    """Test the 'continuity government-pack' CLI command."""
    parser = build_parser()
    pack_dir = tmp_path / "cli-pack"

    key_path = tmp_path / "ed25519-key.pem"
    priv_key = ed25519.Ed25519PrivateKey.generate()
    key_path.write_bytes(
        priv_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    args = parser.parse_args(
        [
            "government-pack",
            "--out",
            str(pack_dir),
            "--key",
            str(key_path),
            "--json",
        ]
    )
    args.func(args)

    assert (pack_dir / "SEALED_EVIDENCE_DIGEST.json").is_file()
    assert (pack_dir / "SBOM_CYCLONEDX.json").is_file()


def test_cli_sbom(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Test the 'continuity sbom' CLI command."""
    parser = build_parser()
    sbom_file = tmp_path / "sbom.json"

    args = parser.parse_args(
        [
            "sbom",
            "--standard",
            "cyclonedx",
            "--out",
            str(sbom_file),
        ]
    )
    args.func(args)

    assert sbom_file.is_file()
    data = json.loads(sbom_file.read_text(encoding="utf-8"))
    assert data["bomFormat"] == "CycloneDX"


def test_cli_verify_compliance(capsys: pytest.CaptureFixture[str]) -> None:
    """Test the 'continuity verify-compliance' CLI command."""
    parser = build_parser()
    args = parser.parse_args(
        [
            "verify-compliance",
            "--profile",
            "all",
            "--json",
        ]
    )
    args.func(args)

    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["verified"] is True
    assert len(res["findings"]) == len(ITSG33_CONTROLS)
    assert res["scif_attestation"]["is_scif_certified"] is True
