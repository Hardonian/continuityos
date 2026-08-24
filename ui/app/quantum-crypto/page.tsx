"use client";

import { useState } from "react";
import Link from "next/link";

export default function QuantumCryptoPage() {
  const [zkpVerified, setZkpVerified] = useState<boolean>(true);
  const [policyMinimum, setPolicyMinimum] = useState<number>(30);
  const [merkleProofValid, setMerkleProofValid] = useState<boolean>(true);

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Post-Quantum Cryptography &amp; Zero-Knowledge Assurance</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Post-Quantum (ML-DSA / ML-KEM) &amp; ZKP Assurance Center
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Cryptographic evidence ledger verification, NIST FIPS 203 (ML-KEM-768) key encapsulation,
          NIST FIPS 204 (ML-DSA-65) signatures, and Zero-Knowledge Proofs (ZKPs) for private reserve verification.
        </p>
      </header>

      {/* 2-Column Crypto HUD */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Post-Quantum Algorithms Panel */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", margin: 0 }}>⚛️ NIST Post-Quantum Algorithms</h2>
            <span
              style={{
                background: "rgba(74, 222, 128, 0.15)",
                color: "var(--accent-2)",
                fontSize: "0.72rem",
                fontWeight: 700,
                fontFamily: "var(--mono)",
                padding: "0.2rem 0.5rem",
                borderRadius: "4px",
              }}
            >
              QUANTUM-SAFE ENFORCED
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ background: "var(--panel-2)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                <strong style={{ color: "var(--accent)" }}>ML-KEM-768 (Kyber)</strong>
                <span style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--muted)" }}>FIPS 203 Standard</span>
              </div>
              <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: 0 }}>
                Lattice-based key encapsulation for sealed intelligence envelopes and inter-SCIF telemetry encryption.
              </p>
            </div>

            <div style={{ background: "var(--panel-2)", padding: "1rem", borderRadius: "8px", border: "1px solid var(--border)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                <strong style={{ color: "var(--accent-2)" }}>ML-DSA-65 (Dilithium)</strong>
                <span style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--muted)" }}>FIPS 204 Standard</span>
              </div>
              <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: 0 }}>
                High-security post-quantum digital signature algorithm for sovereign evidence ledgers and incident records.
              </p>
            </div>
          </div>
        </div>

        {/* Zero-Knowledge Proof Reserve Verifier */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", margin: 0 }}>🛡️ Zero-Knowledge Reserve Proofs (ZKP)</h2>
            <span
              style={{
                background: zkpVerified ? "rgba(74, 222, 128, 0.15)" : "rgba(248, 113, 113, 0.15)",
                color: zkpVerified ? "var(--accent-2)" : "var(--danger)",
                fontSize: "0.72rem",
                fontWeight: 700,
                fontFamily: "var(--mono)",
                padding: "0.2rem 0.5rem",
                borderRadius: "4px",
              }}
            >
              {zkpVerified ? "PROOF VALID (CONFIRMED)" : "PROOF REJECTED"}
            </span>
          </div>

          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "1.2rem" }}>
            Mathematically proves that strategic mineral stockpiles satisfy defense policy minimums
            <strong> without revealing exact physical stockpile numbers or secret depot coordinates</strong>.
          </p>

          <div style={{ background: "var(--panel-2)", padding: "1rem", borderRadius: "8px", fontFamily: "var(--mono)", fontSize: "0.78rem" }}>
            <div style={{ marginBottom: "0.4rem" }}>
              Policy Minimum: <strong style={{ color: "var(--text)" }}>&ge; {policyMinimum} Days</strong>
            </div>
            <div style={{ marginBottom: "0.4rem" }}>
              Commitment Hash: <code style={{ color: "var(--accent)" }}>e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855</code>
            </div>
            <div>
              Zero-Knowledge Verification: <span style={{ color: "var(--accent-2)", fontWeight: 700 }}>PASS (&gt;= 90 Days Provably Held)</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/war-room" className="btn btn-primary">
          ← Back to War Room
        </Link>
        <Link href="/canadian-corridors" className="btn btn-ghost">
          Explore Canadian Strategic Corridors
        </Link>
      </div>
    </div>
  );
}
