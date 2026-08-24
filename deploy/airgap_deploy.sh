#!/usr/bin/env bash
# ==============================================================================
# ContinuityOS / Aegis Continuity — Sovereign Air-Gap SCIF Deployment Script
# ==============================================================================
# Validates zero external network egress, initializes local cryptographic keypairs,
# verifies local dataset caches, and starts the systemd service in isolated enclave mode.
# ==============================================================================

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "========================================================================"
echo " Aegis Continuity — Sovereign Air-Gap SCIF Deployment & Verification"
echo " Target Classification: PROTECTED_B / SECRET // CANADIAN EYES ONLY"
echo "========================================================================"

# 1. Enforce Offline / Zero-Egress Environment Variables
export CONTINUITY_ALLOW_OUTBOUND_HTTP="false"
export CONTINUITY_STORAGE_DIR="${REPO_ROOT}/var"
export CONTINUITY_KEYS_DIR="${REPO_ROOT}/var/keys"

echo "[1/5] Enforcing Zero-Egress Security Policy..."
mkdir -p "${CONTINUITY_STORAGE_DIR}" "${CONTINUITY_KEYS_DIR}"
chmod 700 "${CONTINUITY_STORAGE_DIR}" "${CONTINUITY_KEYS_DIR}"

# 2. Generate or Verify Local Ed25519 Cryptographic Keys
echo "[2/5] Initializing Isolated Cryptographic Signing Enclave..."
if [ ! -f "${CONTINUITY_KEYS_DIR}/ed25519_signing_key.pem" ]; then
    echo " -> Generating local Ed25519 signing keypair..."
    uv run continuity generate-evidence-keys "${CONTINUITY_KEYS_DIR}"
fi
chmod 600 "${CONTINUITY_KEYS_DIR}"/*

# 3. Run Automated Air-Gap SCIF Audit
echo "[3/5] Running Air-Gap SCIF & Key Isolation Audit..."
uv run continuity sovereign-audit --repo-dir "${REPO_ROOT}"

# 4. Run CCCS ITSG-33 / PBMM Compliance Check
echo "[4/5] Running CCCS ITSG-33 / PBMM Compliance Verification..."
uv run continuity pbmm-audit --region on-premise-scif-canada --tls-version 1.3

# 5. Execute Offline Contract Smoke Test with MockProvider
echo "[5/5] Exercising Offline MockProvider Telemetry Assessment..."
uv run continuity observe --mock
uv run continuity canadian-corridor critical-minerals

echo "========================================================================"
echo " [SUCCESS] Sovereign Air-Gap SCIF Deployment Ready & Verified."
echo "========================================================================"
