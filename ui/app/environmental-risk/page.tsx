"use client";

import { useState } from "react";
import Link from "next/link";

export default function EnvironmentalRiskPage() {
  // Permafrost simulator states
  const [ddt, setDdt] = useState<number>(480);
  const [peatCoverCm, setPeatCoverCm] = useState<number>(15);

  // Wildfire simulator states
  const [fwi, setFwi] = useState<number>(32);
  const [fireDistanceKm, setFireDistanceKm] = useState<number>(8);

  // Calculated permafrost settlement
  const rawThawM = Math.sqrt((2.0 * 1.4 * ddt * 86400.0) / (180.0 * 1000000.0));
  const rawThawCm = rawThawM * 100.0;
  const effectiveThawCm = Math.max(0, rawThawCm - peatCoverCm * 0.45);
  const settlementRisk = Math.min(1.0, effectiveThawCm / 120.0);

  const speedLimit = settlementRisk > 0.75 ? 0 : settlementRisk > 0.4 ? 15 : 45;
  const trackStatus =
    settlementRisk > 0.75
      ? "SUSPENDED (CRITICAL THAW)"
      : settlementRisk > 0.4
      ? "SLOW ORDER (15 MPH)"
      : "STABLE (FULL SPEED 45 MPH)";

  // Calculated wildfire risk
  const fwiFactor = Math.min(1.0, fwi / 40.0);
  const proximityFactor = Math.max(0, 1.0 - fireDistanceKm / 30.0);
  const closureProb = Math.min(1.0, (fwiFactor * 0.4 + proximityFactor * 0.6) * 1.3);
  const visibilityLoss = Math.min(95, fwiFactor * 30.0 + proximityFactor * 60.0);

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Geographic, Environmental &amp; Climate Infrastructure</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Permafrost Thaw &amp; Wildfire Corridor Risk Dashboard
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Physics-based active-layer permafrost degradation modeling for northern rail links, Canadian Fire
          Weather Index (FWI) corridor impingement, and transatlantic subsea infrastructure acoustic security.
        </p>
      </header>

      {/* Grid: Permafrost & Wildfire Simulators */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Permafrost Thaw Embankment Simulator */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", margin: 0 }}>❄️ Hudson Bay Railway Permafrost Model</h2>
            <span
              style={{
                background:
                  speedLimit === 45
                    ? "rgba(74, 222, 128, 0.15)"
                    : speedLimit === 15
                    ? "rgba(251, 191, 36, 0.15)"
                    : "rgba(248, 113, 113, 0.15)",
                color:
                  speedLimit === 45 ? "var(--accent-2)" : speedLimit === 15 ? "var(--accent-3)" : "var(--danger)",
                fontFamily: "var(--mono)",
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "0.2rem 0.5rem",
                borderRadius: "4px",
              }}
            >
              {trackStatus}
            </span>
          </div>

          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "1.2rem" }}>
            Simulates subarctic active-layer thaw penetration across discontinuous permafrost subgrade
            (The Pas $\to$ Thompson $\to$ Port of Churchill).
          </p>

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Degree-Days of Thaw (DDT): <strong style={{ color: "var(--text)" }}>{ddt} °C·days</strong>
            </label>
            <input
              type="range"
              min="100"
              max="900"
              value={ddt}
              onChange={(e) => setDdt(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--accent)" }}
            />
          </div>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Insulating Organic Peat Cover: <strong style={{ color: "var(--text)" }}>{peatCoverCm} cm</strong>
            </label>
            <input
              type="range"
              min="0"
              max="40"
              value={peatCoverCm}
              onChange={(e) => setPeatCoverCm(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--accent)" }}
            />
          </div>

          <div
            style={{
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "1rem",
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
            }}
          >
            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                EFFECTIVE THAW DEPTH
              </div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--accent)" }}>
                {effectiveThawCm.toFixed(1)} cm
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                SETTLEMENT RISK SCORE
              </div>
              <div
                style={{
                  fontSize: "1.4rem",
                  fontWeight: 800,
                  color: settlementRisk > 0.7 ? "var(--danger)" : "var(--accent-2)",
                }}
              >
                {(settlementRisk * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>

        {/* Wildfire Corridor Risk Model */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", margin: 0 }}>🔥 Trans-Canada Wildfire Model</h2>
            <span
              style={{
                background: closureProb > 0.65 ? "rgba(248, 113, 113, 0.15)" : "rgba(74, 222, 128, 0.15)",
                color: closureProb > 0.65 ? "var(--danger)" : "var(--accent-2)",
                fontFamily: "var(--mono)",
                fontSize: "0.75rem",
                fontWeight: 700,
                padding: "0.2rem 0.5rem",
                borderRadius: "4px",
              }}
            >
              CLOSURE PROB: {(closureProb * 100).toFixed(0)}%
            </span>
          </div>

          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "1.2rem" }}>
            Fuses Canadian Forest Fire Weather Index (FWI) components with satellite hot-spot polygons across
            the Fraser Canyon and Rogers Pass mainlines.
          </p>

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Fire Weather Index (FWI): <strong style={{ color: "var(--text)" }}>{fwi}</strong>
            </label>
            <input
              type="range"
              min="5"
              max="50"
              value={fwi}
              onChange={(e) => setFwi(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--accent-3)" }}
            />
          </div>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Distance to Closest Fire Front: <strong style={{ color: "var(--text)" }}>{fireDistanceKm} km</strong>
            </label>
            <input
              type="range"
              min="1"
              max="40"
              value={fireDistanceKm}
              onChange={(e) => setFireDistanceKm(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--accent-3)" }}
            />
          </div>

          <div
            style={{
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "1rem",
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
            }}
          >
            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                VISIBILITY REDUCTION
              </div>
              <div style={{ fontSize: "1.4rem", fontWeight: 800, color: "var(--accent-3)" }}>
                {visibilityLoss.toFixed(0)}%
              </div>
            </div>
            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--muted)", fontFamily: "var(--mono)" }}>
                ACTION DIRECTIVE
              </div>
              <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text)", marginTop: "0.2rem" }}>
                {closureProb > 0.65 ? "Initiate Modal Rail Bypass" : "Station Water Tenders"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Subsea Cable & Seabed Energy Conduit Security */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ fontSize: "1.3rem", marginBottom: "0.8rem" }}>
          🌊 Atlantic Subsea Optical Trunk &amp; Seabed Energy Conduit Integrity
        </h2>
        <p style={{ color: "var(--muted)", fontSize: "0.9rem", marginBottom: "1.2rem" }}>
          Acoustic anomaly detection and anchoring hazard exclusion monitoring along the Halifax and Cabot
          Strait subsea landing corridors.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "1rem" }}>
          {[
            {
              id: "SUBSEA-TRUNK-01",
              name: "Hibernia Express Transatlantic Fiber",
              depth: "1,240m Depth",
              status: "NOMINAL",
              acousticAnomaly: "+2.1 dB",
              anchorBuffer: "18.4 km clear",
            },
            {
              id: "CABOT-STRAIT-02",
              name: "Cabot Strait High-Voltage Subsea Intertie",
              depth: "480m Depth",
              status: "NOMINAL",
              acousticAnomaly: "+3.8 dB",
              anchorBuffer: "12.2 km clear",
            },
            {
              id: "SCOTIAN-SHELF-03",
              name: "Scotian Shelf Hydrophone Array Node",
              depth: "85m Depth",
              status: "ATTENTION",
              acousticAnomaly: "+14.2 dB",
              anchorBuffer: "3.1 km (Loitering Vessel)",
            },
          ].map((item) => (
            <div
              key={item.id}
              style={{
                background: "var(--panel-2)",
                border: item.status === "ATTENTION" ? "1px solid rgba(251, 191, 36, 0.4)" : "1px solid var(--border)",
                borderRadius: "8px",
                padding: "1.2rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.4rem" }}>
                <strong style={{ fontSize: "0.95rem" }}>{item.name}</strong>
                <span
                  style={{
                    background:
                      item.status === "NOMINAL" ? "rgba(74, 222, 128, 0.15)" : "rgba(251, 191, 36, 0.15)",
                    color: item.status === "NOMINAL" ? "var(--accent-2)" : "var(--accent-3)",
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    padding: "0.15rem 0.4rem",
                    borderRadius: "4px",
                    fontFamily: "var(--mono)",
                  }}
                >
                  {item.status}
                </span>
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.5rem" }}>
                📍 {item.depth} • Sensor: Seafloor Hydrophones
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--accent)", fontFamily: "var(--mono)" }}>
                Acoustic: {item.acousticAnomaly} • Anchor Buffer: {item.anchorBuffer}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/counter-intel" className="btn btn-primary">
          ← Back to Counter-Intelligence HUD
        </Link>
        <Link href="/canadian-corridors" className="btn btn-ghost">
          Explore Canadian Corridors
        </Link>
      </div>
    </div>
  );
}
