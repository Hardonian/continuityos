# SCIF Hardware Attestation & Air-Gap Hardening Guide

## 1. Scope & Purpose

This guide defines the hardening, attestation, and operational protocols for deploying Aegis Continuity within Sensitive Compartmented Information Facilities (SCIF) and air-gapped Tactical Operations Centers (TOC).

---

## 2. Hardware Root of Trust & TPM 2.0 PCR Validation

Aegis Continuity validates hardware integrity against NIST SP 800-155 / SP 800-147 guidelines:

- **PCR[0]**: Measures Core Root of Trust for Measurement (CRTM) and UEFI BIOS firmware code.
- **PCR[2] & PCR[4]**: Measures Option ROMs and UEFI Boot Manager execution code.
- **PCR[7]**: Measures Secure Boot state and OEM platform certificates.

### Attestation Verification

Execute local hardware PCR attestation via CLI:

```bash
continuity scif-attest --facility-id SCIF-HQ-OTTAWA --facility-name "DND Carling Campus SCIF"
```

---

## 3. Zero-Egress Physical Network Isolation

- **Kernel Network Namespace Isolation**: All daemon processes bind strictly to `127.0.0.1`.
- **Socket Audit**: Automated scans verify that zero non-loopback outbound TCP/UDP sockets are opened.
- **Data Diode & Sneakernet Exchange**: Cross-enclave synchronization occurs via unidirectional optical data diodes or encrypted hardware tokens carrying signed delta logs.

---

## 4. Deterministic Memory Zeroization & Anti-Forensics

- **CSPRNG Overwrite**: Volatile Ed25519 private keys, ML-KEM session keys, and unsealed intel are overwritten with cryptographic entropy immediately after use or on process termination (`SIGTERM`, `SIGINT`, panics).
- **Cold Boot Attack Mitigation**: Prevents residual DRAM key recovery through proactive memory scrubbing.
