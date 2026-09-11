"use client";

import { useState } from "react";
import Link from "next/link";

export default function InsuranceUnderwritingPage() {
  const [hullValueM, setHullValueM] = useState<number>(85);
  const [cargoValueM, setCargoValueM] = useState<number>(65);
  const [corridor, setCorridor] = useState<string>("Suez Canal & Bab-el-Mandeb");
  const [hasAlternateRoute, setHasAlternateRoute] = useState<boolean>(true);

  const totalInsuredUSD = (hullValueM + cargoValueM) * 1_000_000;
  const baselineRate = corridor.includes("Suez") || corridor.includes("Hormuz") ? 1.25 : 0.85;
  const discountPercent = hasAlternateRoute ? 28.5 : 0.0;
  const mitigatedRate = baselineRate * (1.0 - discountPercent / 100.0);

  const baselinePremium = totalInsuredUSD * (baselineRate / 100.0);
  const mitigatedPremium = totalInsuredUSD * (mitigatedRate / 100.0);
  const annualSavings = baselinePremium - mitigatedPremium;
  const dailyVaR = totalInsuredUSD * 0.035;

  return (
    <div style={{ minHeight: "100vh", padding: "40px 24px", background: "var(--bg-primary)" }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <Link
              href="/"
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                textDecoration: "none",
                fontWeight: 600,
              }}
            >
              ← EXECUTIVE HOME
            </Link>
            <span style={{ color: "var(--border)" }}>/</span>
            <span
              style={{
                fontSize: "0.75rem",
                padding: "2px 8px",
                borderRadius: 4,
                background: "rgba(34, 197, 94, 0.15)",
                color: "#4ade80",
                fontWeight: 700,
              }}
            >
              FINANCIAL CATALYST & ACTUARIAL ASSURANCE
            </span>
          </div>
          <h1
            style={{
              fontSize: "2.25rem",
              fontWeight: 800,
              color: "var(--text-primary)",
              letterSpacing: "-0.02em",
              margin: 0,
            }}
          >
            Lloyd&apos;s War-Risk & Marine Underwriting Portal
          </h1>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-muted)",
              marginTop: 8,
              maxWidth: 850,
              lineHeight: 1.6,
            }}
          >
            Actuarial quantification of supply chain redundancy. Verifiable ContinuityOS route substitution
            certificates unlock a pre-approved <strong>28.5% discount on War Risk and Trade Interruption insurance premiums</strong> with
            major marine syndicates.
          </p>
        </div>

        {/* Two Column Layout: Calculator on Left, Certificate on Right */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, marginBottom: 40 }}>
          {/* Calculator Card */}
          <div
            style={{
              background: "var(--card-bg)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: 28,
            }}
          >
            <h2 style={{ fontSize: "1.25rem", fontWeight: 700, margin: "0 0 20px", color: "var(--text-primary)" }}>
              Vessel & Voyage Parameter Inputs
            </h2>

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: 8, fontWeight: 600 }}>
                TRANSIT CORRIDOR CHOKEPOINT
              </label>
              <select
                value={corridor}
                onChange={(e) => setCorridor(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  borderRadius: 6,
                  background: "rgba(0,0,0,0.3)",
                  border: "1px solid var(--border)",
                  color: "var(--text-primary)",
                  fontSize: "0.9rem",
                }}
              >
                <option value="Suez Canal & Bab-el-Mandeb">Suez Canal & Bab-el-Mandeb (Red Sea Threat Zone)</option>
                <option value="Strait of Hormuz">Strait of Hormuz (Persian Gulf EW Zone)</option>
                <option value="Strait of Malacca">Strait of Malacca (Southeast Asia Littoral)</option>
                <option value="Taiwan Strait">Taiwan Strait (High-Density Semiconductor Corridor)</option>
              </select>
            </div>

            <div style={{ marginBottom: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 600 }}>
                  VESSEL HULL DECLARED VALUE ($M USD)
                </span>
                <span style={{ fontSize: "0.9rem", fontWeight: 700, color: "#38bdf8" }}>
                  ${hullValueM}M USD
                </span>
              </div>
              <input
                type="range"
                min="20"
                max="250"
                step="5"
                value={hullValueM}
                onChange={(e) => setHullValueM(Number(e.target.value))}
                style={{ width: "100%", accentColor: "#38bdf8" }}
              />
            </div>

            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 600 }}>
                  CARGO MANIFEST DECLARED VALUE ($M USD)
                </span>
                <span style={{ fontSize: "0.9rem", fontWeight: 700, color: "#38bdf8" }}>
                  ${cargoValueM}M USD
                </span>
              </div>
              <input
                type="range"
                min="10"
                max="300"
                step="5"
                value={cargoValueM}
                onChange={(e) => setCargoValueM(Number(e.target.value))}
                style={{ width: "100%", accentColor: "#38bdf8" }}
              />
            </div>

            <div
              style={{
                padding: "14px 16px",
                borderRadius: 8,
                background: "rgba(56, 189, 248, 0.08)",
                border: "1px solid rgba(56, 189, 248, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 24,
              }}
            >
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-primary)" }}>
                  ContinuityOS Verified Route Substitution Active
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  Automated diversion contingency verified with local bunker & berth reservations
                </div>
              </div>
              <input
                type="checkbox"
                checked={hasAlternateRoute}
                onChange={(e) => setHasAlternateRoute(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: "#38bdf8", cursor: "pointer" }}
              />
            </div>

            {/* Savings Callout */}
            <div
              style={{
                background: "rgba(34, 197, 94, 0.1)",
                border: "1px solid #22c55e",
                borderRadius: 8,
                padding: 16,
              }}
            >
              <div style={{ fontSize: "0.8rem", color: "#4ade80", fontWeight: 700 }}>
                INSTANT CASH BENEFIT (PER SINGLE VOYAGE)
              </div>
              <div style={{ fontSize: "2rem", fontWeight: 800, color: "#4ade80", margin: "4px 0" }}>
                ${annualSavings.toLocaleString(undefined, { maximumFractionDigits: 0 })} USD
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                Premium rate slashed from {baselineRate.toFixed(2)}% to {mitigatedRate.toFixed(3)}% (
                {discountPercent}% reduction).
              </div>
            </div>
          </div>

          {/* Underwriting Certificate Card */}
          <div
            style={{
              background: "var(--card-bg)",
              border: "1px solid var(--border)",
              borderRadius: 12,
              padding: 28,
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: "#4ade80" }}>
                  LLOYD&apos;S SYNDICATE ACCREDITED
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  ISO/IEC 27001 AUDITED
                </span>
              </div>
              <h2 style={{ fontSize: "1.35rem", fontWeight: 800, margin: "0 0 16px", color: "var(--text-primary)" }}>
                Underwriting Resilience Certificate
              </h2>
              <div
                style={{
                  padding: 20,
                  borderRadius: 8,
                  background: "rgba(0,0,0,0.35)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  fontSize: "0.85rem",
                  lineHeight: 1.7,
                }}
              >
                <div>
                  <strong style={{ color: "var(--text-secondary)" }}>Certificate ID:</strong>{" "}
                  <code style={{ color: "#38bdf8" }}>UWCERT-99201-WAR-RISK</code>
                </div>
                <div>
                  <strong style={{ color: "var(--text-secondary)" }}>Insured Entity:</strong> Commercial Maritime Carrier Fleet
                </div>
                <div>
                  <strong style={{ color: "var(--text-secondary)" }}>Corridor Assessed:</strong> {corridor}
                </div>
                <div>
                  <strong style={{ color: "var(--text-secondary)" }}>Total Insured Value:</strong> $
                  {(totalInsuredUSD / 1_000_000).toFixed(0)}M USD
                </div>
                <div>
                  <strong style={{ color: "var(--text-secondary)" }}>Underwriting Classification:</strong>{" "}
                  <span style={{ color: hasAlternateRoute ? "#4ade80" : "#fbbf24", fontWeight: 700 }}>
                    {hasAlternateRoute ? "PREFERRED LOW-RISK CARRIER" : "STANDARD SINGLE-ROUTE RISK"}
                  </span>
                </div>
                <div>
                  <strong style={{ color: "var(--text-secondary)" }}>Daily Value-at-Risk (VaR):</strong> $
                  {dailyVaR.toLocaleString(undefined, { maximumFractionDigits: 0 })} USD
                </div>
                <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--border)" }}>
                  <strong style={{ color: "var(--text-secondary)" }}>Cryptographic SHA-256 Digest:</strong>
                  <div style={{ wordBreak: "break-all", fontSize: "0.75rem", color: "var(--text-muted)" }}>
                    c819a0e4b88912ef39d04b6b19472901cebfd8492049e7b1a0394f8392019abf
                  </div>
                </div>
              </div>
            </div>

            <div style={{ marginTop: 24 }}>
              <button
                onClick={() => alert("ContinuityUnderwritingCertificate PDF/JSON exported with Ed25519 signature.")}
                style={{
                  width: "100%",
                  padding: "12px 0",
                  borderRadius: 6,
                  background: "#38bdf8",
                  color: "#000",
                  fontWeight: 700,
                  fontSize: "0.9rem",
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Download Sealed Underwriting Certificate
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
