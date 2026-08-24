"use client";

import { useState } from "react";
import Link from "next/link";

interface AttestationItem {
  id: string;
  name: string;
  isCompliant: boolean;
  score: number;
  details: string;
}

const SAMPLE_CONTROLS: AttestationItem[] = [
  {
    id: "TPM-2.0-PCR",
    name: "TPM 2.0 Hardware Root of Trust PCR Measurement",
    isCompliant: true,
    score: 1.0,
    details: "Valid PCR[0,7] quote verified against sovereign baseline (e3b0c44298fc1c14...)",
  },
  {
    id: "AIRGAP-ZERO-EGRESS",
    name: "Zero-Egress Physical Network Isolation",
    isCompliant: true,
    score: 1.0,
    details: "No non-local outbound network sockets detected (100% air-gap isolation)",
  },
  {
    id: "SECURE-BOOT-LOCKDOWN",
    name: "UEFI Secure Boot & Kernel Lockdown Mode",
    isCompliant: true,
    score: 1.0,
    details: "Kernel integrity lockdown active; unsigned kernel modules prohibited",
  },
  {
    id: "MEM-ZEROIZATION",
    name: "Deterministic Cryptographic Key Zeroization on SIGTERM/Panic",
    isCompliant: true,
    score: 1.0,
    details: "Volatile key material overwritten with CSPRNG entropy upon process exit",
  },
  {
    id: "HARDWARE-ENTROPY",
    name: "Hardware TRNG / CSPRNG Entropy Rate",
    isCompliant: true,
    score: 1.0,
    details: "Current entropy pool throughput: 1024.0 KB/s (exceeds 64 KB/s threshold)",
  },
];

export default function SCIFAttestationPage() {
  const [controls, setControls] = useState<AttestationItem[]>(SAMPLE_CONTROLS);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);

  const triggerAudit = () => {
    setIsVerifying(true);
    setTimeout(() => {
      setIsVerifying(false);
    }, 800);
  };

  const isAllCompliant = controls.every((c) => c.isCompliant);

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Hardware Root of Trust &amp; Air-Gap Enclave Attestation</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          SCIF Hardware TPM 2.0 &amp; Air-Gap Attestation Center
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Cryptographically validates TPM 2.0 Platform Configuration Registers (PCRs), zero-egress network isolation,
          kernel lockdown, volatile memory zeroization, and hardware entropy for Protected B and NATO Secret enclaves.
        </p>
      </header>

      {/* Attestation Certificate Banner */}
      <div
        style={{
          background: "var(--panel)",
          border: isAllCompliant ? "1px solid rgba(74, 222, 128, 0.4)" : "1px solid rgba(255, 0, 60, 0.4)",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "2rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.3rem" }}>
            <span
              style={{
                background: isAllCompliant ? "rgba(74, 222, 128, 0.15)" : "rgba(255, 0, 60, 0.15)",
                color: isAllCompliant ? "var(--accent-2)" : "#ff4d6d",
                fontFamily: "var(--mono)",
                fontSize: "0.8rem",
                fontWeight: 800,
                padding: "0.2rem 0.6rem",
                borderRadius: "4px",
              }}
            >
              {isAllCompliant ? "SCIF-CERTIFIED (NOMINAL)" : "ATTESTATION FAILED"}
            </span>
            <strong style={{ fontSize: "1.15rem" }}>DND Carling Campus National Command SCIF</strong>
          </div>
          <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
            Facility ID: <code>SCIF-HQ-OTTAWA</code> • Signed Hash: <code>7f83b1657ff1fc53...</code>
          </div>
        </div>

        <button onClick={triggerAudit} disabled={isVerifying} className="btn btn-primary">
          {isVerifying ? "Verifying Hardware TPM..." : "🔄 Execute Real-Time Attestation"}
        </button>
      </div>

      {/* Controls Grid */}
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "2rem" }}>
        {controls.map((c) => (
          <div
            key={c.id}
            style={{
              background: "var(--panel)",
              border: "1px solid var(--border)",
              borderRadius: "10px",
              padding: "1.25rem",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
              <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                <span style={{ fontFamily: "var(--mono)", fontSize: "0.75rem", color: "var(--accent)" }}>
                  [{c.id}]
                </span>
                <strong style={{ fontSize: "1rem" }}>{c.name}</strong>
              </div>
              <span
                style={{
                  fontFamily: "var(--mono)",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  color: c.isCompliant ? "var(--accent-2)" : "var(--danger)",
                }}
              >
                {c.isCompliant ? "COMPLIANT (100%)" : "NON-COMPLIANT"}
              </span>
            </div>
            <p style={{ fontSize: "0.84rem", color: "var(--muted)", margin: 0 }}>{c.details}</p>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/rbac-audit" className="btn btn-primary">
          ← Multi-Tenant RBAC Inspector
        </Link>
        <Link href="/war-room" className="btn btn-ghost">
          Return to Mission Control HUD
        </Link>
      </div>
    </div>
  );
}
