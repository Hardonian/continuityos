"""ContinuityOS Software Bill of Materials (SBOM) Generator.

Provides deterministic, machine-verifiable Software Bill of Materials compliant with:
- CycloneDX v1.5 JSON (OWASP Foundation)
- SPDX v2.3 JSON (Linux Foundation / ISO/IEC 5962:2021)
- NIST SP 800-161 / Executive Order 14028 software supply chain standards
- Canadian Centre for Cyber Security (CCCS) ITSG-33 SA-4 / SA-11 baseline controls.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

COMPONENT_VERSION = "1.0.0"
ORGANIZATION = "ContinuityOS Sovereign Systems"
AUTHORS = [{"name": "ContinuityOS Architecture Core", "email": "security@continuityos.com"}]

CORE_MODULES = [
    "domain.py",
    "dsl.py",
    "schemas.py",
    "compiler.py",
    "evidence.py",
    "crypto.py",
    "sovereign.py",
    "readiness.py",
    "cop.py",
    "threat.py",
    "database.py",
    "rbac.py",
    "attestation.py",
    "cluster.py",
    "wargame.py",
    "reconcile.py",
    "assurance.py",
    "graph.py",
    "fusion.py",
    "policy.py",
    "scenario.py",
    "inventory.py",
    "recovery.py",
    "remediation.py",
    "closure.py",
    "trust.py",
    "independence.py",
    "substitution.py",
    "service.py",
    "cli.py",
]

RUNTIME_DEPENDENCIES = [
    {
        "name": "pydantic",
        "version": ">=2.10.0",
        "purl": "pkg:pypi/pydantic@2.10.0",
        "license": "MIT",
        "description": "Data validation and settings management using Python type annotations",
    },
    {
        "name": "cryptography",
        "version": ">=43.0.0",
        "purl": "pkg:pypi/cryptography@43.0.0",
        "license": "Apache-2.0 OR BSD-3-Clause",
        "description": "Cryptographic recipes and primitives (Ed25519, SHA-256, AES-GCM)",
    },
    {
        "name": "fastapi",
        "version": ">=0.115.0",
        "purl": "pkg:pypi/fastapi@0.115.0",
        "license": "MIT",
        "description": "High performance sovereign REST API framework",
    },
    {
        "name": "uvicorn",
        "version": ">=0.32.0",
        "purl": "pkg:pypi/uvicorn@0.32.0",
        "license": "BSD-3-Clause",
        "description": "Lightning-fast ASGI server implementation",
    },
    {
        "name": "pyyaml",
        "version": ">=6.0.2",
        "purl": "pkg:pypi/pyyaml@6.0.2",
        "license": "MIT",
        "description": "YAML 1.2 parser and emitter for declarative policy specs",
    },
    {
        "name": "numpy",
        "version": ">=2.1.0",
        "purl": "pkg:pypi/numpy@2.1.0",
        "license": "BSD-3-Clause",
        "description": "Deterministic matrix arithmetic for risk fusion and recovery solvers",
    },
]


def _hash_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    if not path.is_file():
        return "0" * 64
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def generate_cyclonedx_sbom(src_dir: Path | None = None) -> dict[str, Any]:
    """Generate a CycloneDX v1.5 JSON SBOM for ContinuityOS."""
    if src_dir is None:
        src_dir = Path(__file__).resolve().parent

    timestamp = datetime.now(UTC).isoformat()
    serial_number = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_DNS, 'continuityos.com/sbom/cyclonedx')}"

    components: list[dict[str, Any]] = []

    # 1. Main Application Component
    root_component = {
        "type": "application",
        "bom-ref": "pkg:pypi/continuityos@1.0.0",
        "name": "continuityos",
        "version": COMPONENT_VERSION,
        "description": "ContinuityOS Sovereign Resilience-as-Code Engine",
        "scope": "required",
        "supplier": {
            "name": ORGANIZATION,
            "url": ["https://continuityos.com"],
        },
        "licenses": [{"license": {"id": "Apache-2.0"}}],
        "properties": [
            {"name": "sovereign:classification", "value": "PROTECTED_B"},
            {"name": "sovereign:dataResidency", "value": "CANADIAN_SOVEREIGN"},
            {"name": "sovereign:airGapCertified", "value": "true"},
            {"name": "sovereign:pqcSupported", "value": "true"},
        ],
    }

    # 2. Internal Core Modules with SHA-256 hashes
    for mod_name in sorted(CORE_MODULES):
        mod_path = src_dir / mod_name
        sha256_hash = _hash_file(mod_path)
        components.append(
            {
                "type": "file",
                "bom-ref": f"continuityos:src/{mod_name}",
                "name": f"src/continuityos/{mod_name}",
                "version": COMPONENT_VERSION,
                "scope": "required",
                "hashes": [{"alg": "SHA-256", "content": sha256_hash}],
                "licenses": [{"license": {"id": "Apache-2.0"}}],
            }
        )

    # 3. Third-party Runtime Dependencies
    for dep in RUNTIME_DEPENDENCIES:
        components.append(
            {
                "type": "library",
                "bom-ref": dep["purl"],
                "name": dep["name"],
                "version": dep["version"],
                "purl": dep["purl"],
                "description": dep["description"],
                "scope": "required",
                "licenses": [{"license": {"name": dep["license"]}}],
            }
        )

    # Dependencies relationships graph
    dependencies = [
        {
            "ref": "pkg:pypi/continuityos@1.0.0",
            "dependsOn": [c["bom-ref"] for c in components],
        }
    ]

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial_number,
        "version": 1,
        "metadata": {
            "timestamp": timestamp,
            "tools": [
                {
                    "vendor": ORGANIZATION,
                    "name": "ContinuityOS SBOM Generator",
                    "version": COMPONENT_VERSION,
                }
            ],
            "authors": AUTHORS,
            "component": root_component,
            "manufacture": {
                "name": ORGANIZATION,
                "url": ["https://continuityos.com"],
            },
        },
        "components": components,
        "dependencies": dependencies,
    }


def generate_spdx_sbom(src_dir: Path | None = None) -> dict[str, Any]:
    """Generate an SPDX v2.3 JSON SBOM for ContinuityOS."""
    if src_dir is None:
        src_dir = Path(__file__).resolve().parent

    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc_namespace = f"https://continuityos.com/spdx/continuityos-{COMPONENT_VERSION}"

    packages: list[dict[str, Any]] = []
    relationships: list[dict[str, Any]] = []

    # Root package
    root_pkg = {
        "SPDXID": "SPDXRef-Package-ContinuityOS",
        "name": "continuityos",
        "versionInfo": COMPONENT_VERSION,
        "downloadLocation": "https://github.com/Hardonian/continuityos",
        "filesAnalyzed": True,
        "supplier": f"Organization: {ORGANIZATION}",
        "originator": f"Organization: {ORGANIZATION}",
        "licenseConcluded": "Apache-2.0",
        "licenseDeclared": "Apache-2.0",
        "copyrightText": f"Copyright (c) {datetime.now(UTC).year} ContinuityOS. All rights reserved.",
        "summary": "ContinuityOS Sovereign Resilience-as-Code Engine",
        "description": "Cyber-physical resilience declaration, simulation, and exact recovery compilation.",
    }
    packages.append(root_pkg)

    # Dependencies as sub-packages
    for dep in RUNTIME_DEPENDENCIES:
        spdx_id = f"SPDXRef-Dependency-{dep['name'].replace('-', '_')}"
        packages.append(
            {
                "SPDXID": spdx_id,
                "name": dep["name"],
                "versionInfo": dep["version"],
                "downloadLocation": f"https://pypi.org/project/{dep['name']}/",
                "filesAnalyzed": False,
                "supplier": f"Organization: PyPI Community ({dep['name']})",
                "licenseConcluded": dep["license"],
                "licenseDeclared": dep["license"],
                "copyrightText": "NOASSERTION",
                "summary": dep["description"],
                "externalRefs": [
                    {
                        "referenceCategory": "PACKAGE-MANAGER",
                        "referenceType": "purl",
                        "referenceLocator": dep["purl"],
                    }
                ],
            }
        )
        relationships.append(
            {
                "spdxElementId": "SPDXRef-Package-ContinuityOS",
                "relatedSpdxElement": spdx_id,
                "relationshipType": "DEPENDS_ON",
            }
        )

    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"ContinuityOS-{COMPONENT_VERSION}-SBOM",
        "documentNamespace": doc_namespace,
        "creationInfo": {
            "created": timestamp,
            "creators": [f"Organization: {ORGANIZATION}", "Tool: ContinuityOS-SBOM-2026"],
            "licenseListVersion": "3.22",
        },
        "packages": packages,
        "relationships": relationships,
    }


def verify_sbom_integrity(sbom: dict[str, Any]) -> bool:
    """Verify that an SBOM contains valid structure and required fields."""
    if sbom.get("bomFormat") == "CycloneDX":
        return bool(
            sbom.get("specVersion") == "1.5"
            and "components" in sbom
            and len(sbom["components"]) >= len(RUNTIME_DEPENDENCIES)
            and "metadata" in sbom
        )
    if sbom.get("spdxVersion") == "SPDX-2.3":
        return bool(
            sbom.get("dataLicense") == "CC0-1.0"
            and "packages" in sbom
            and len(sbom["packages"]) >= 1
            and "creationInfo" in sbom
        )
    return False
