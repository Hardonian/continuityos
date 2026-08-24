"use client";

import { useState } from "react";
import Link from "next/link";

interface WarRoomIncident {
  id: string;
  time: string;
  domain: "MARITIME" | "SPACE" | "ENVIRONMENTAL" | "CYBER" | "MINERALS";
  severity: "INFO" | "WARNING" | "CRITICAL" | "EMERGENCY";
  title: string;
  location: string;
  impactScore: number;
}

const INITIAL_INCIDENTS: WarRoomIncident[] = [
  {
    id: "INC-CAN-9021",
    time: "18:12:04Z",
    domain: "MARITIME",
    severity: "CRITICAL",
    title: "Dark Fleet Transponder Anomaly near Cabot Strait",
    location: "Gulf of St. Lawrence Chokepoint (48.4°N, 64.2°W)",
    impactScore: 0.88,
  },
  {
    id: "INC-CAN-9022",
    time: "18:05:19Z",
    domain: "SPACE",
    severity: "WARNING",
    title: "Gaofen-3 Polar SAR Satellite Recon Pass Window Detected",
    location: "Arctic Northwest Passage Defense Corridor",
    impactScore: 0.72,
  },
  {
    id: "INC-CAN-9023",
    time: "17:58:45Z",
    domain: "ENVIRONMENTAL",
    severity: "WARNING",
    title: "Hudson Bay Railway Trackbed Peat Thaw Differential Settlement",
    location: "Wikusko Bog Subgrade Zone, MB (56.5°N)",
    impactScore: 0.65,
  },
  {
    id: "INC-CAN-9024",
    time: "17:42:11Z",
    domain: "MINERALS",
    severity: "INFO",
    title: "Ring of Fire High-Grade Chromite & Nickel Winter Road Open",
    location: "Nakina Railhead Corridor, Northern ON",
    impactScore: 0.15,
  },
];

export default function WarRoomPage() {
  const [incidents, setIncidents] = useState<WarRoomIncident[]>(INITIAL_INCIDENTS);
  const [selectedScenario, setSelectedScenario] = useState<string>("MARITIME_BLOCKADE");
  const [adversaryPressure, setAdversaryPressure] = useState<number>(0.75);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  const triggerIncidentInject = (domain: "MARITIME" | "CYBER" | "ENVIRONMENTAL" | "SPACE" | "MINERALS") => {
    const now = new Date().toISOString().substring(11, 19) + "Z";
    const newInc: WarRoomIncident = {
      id: `INC-INJECT-${Math.floor(Math.random() * 9000 + 1000)}`,
      time: now,
      domain,
      severity: "EMERGENCY",
      title:
        domain === "CYBER"
          ? "SCADA Flood & GNSS EW Spoofing Attack on Port of Montreal"
          : domain === "MARITIME"
          ? "Transatlantic Subsea Cable Drag-Anchor Physical Sever Risk"
          : domain === "ENVIRONMENTAL"
          ? "Fraser Canyon Rail Wildfire Flame Front Closure (<4km buffer)"
          : domain === "SPACE"
          ? "Unannounced Foreign Radar Satellite Overflight (85° Max Elevation)"
          : "Critical Mineral Ferrochrome Export Embargo Imposed",
      location: "Strategic Canadian Defense Supply Hub",
      impactScore: 0.94,
    };
    setIncidents([newInc, ...incidents.slice(0, 7)]);
  };

  return (
    <div style={{ padding: "1.5rem 0" }}>
      {/* Top Banner Marking */}
      <div
        style={{
          background: "#1a0005",
          border: "1px solid #ff003c",
          color: "#ff4d6d",
          padding: "0.5rem 1rem",
          fontFamily: "var(--mono)",
          fontSize: "0.85rem",
          fontWeight: 700,
          textAlign: "center",
          letterSpacing: "0.15em",
          borderRadius: "6px",
          marginBottom: "1.5rem",
        }}
      >
        🇨🇦 NATIONAL CONTINUITY WAR ROOM // DEFENSE READINESS LEVEL 2 // SECRET // CANADIAN EYES ONLY
      </div>

      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Real-Time Multi-Domain Sovereign Defense Operations</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Strategic National War Room &amp; Mission Continuity HUD
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Live game-theoretic disruption modeling, real-time multi-domain incident streaming, and
          NATO-aligned Strategic Option Trees (SOT) for strategic mineral, logistics, and corridor defense.
        </p>
      </header>

      {/* Grid: 4 Top KPI Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
            SOVEREIGN DEFENSE READINESS
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-2)", margin: "0.3rem 0" }}>
            NATO C-1 / DRRS-A
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>Fully Mission Capable (94.2%)</div>
        </div>

        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
            STRATEGIC MINERAL ENDURANCE
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-3)", margin: "0.3rem 0" }}>
            112 Days Stockpile
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>Class-1 Nickel &amp; Rare Earths</div>
        </div>

        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
            DDIL SCIF MESH STATUS
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent)", margin: "0.3rem 0" }}>
            3 Nodes Synced
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>Ottawa, Halifax &amp; Esquimalt</div>
        </div>

        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
            ACTIVE THREAT INJECTS
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--danger)", margin: "0.3rem 0" }}>
            {incidents.filter((i) => i.severity === "CRITICAL" || i.severity === "EMERGENCY").length} Critical
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>Live sensor alarms triggered</div>
        </div>
      </div>

      {/* Main Two-Column War Room Interface */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Left Panel: Real-Time Telemetry Stream & Live Injector */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", margin: 0 }}>🚨 Live Sovereign Event Stream (SSE)</h2>
            <span style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--accent-2)" }}>
              ● STREAM ACTIVE (100% AIR-GAP ISOLATED)
            </span>
          </div>

          {/* Quick Incident Injects */}
          <div style={{ marginBottom: "1.2rem" }}>
            <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginBottom: "0.5rem" }}>
              ⚡ Tactical Scenario Injections (Defensive Resilience Stress-Testing):
            </div>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <button
                onClick={() => triggerIncidentInject("CYBER")}
                className="btn btn-ghost"
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
              >
                + Cyber SCADA Attack
              </button>
              <button
                onClick={() => triggerIncidentInject("MARITIME")}
                className="btn btn-ghost"
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
              >
                + Subsea Cable Sever
              </button>
              <button
                onClick={() => triggerIncidentInject("ENVIRONMENTAL")}
                className="btn btn-ghost"
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
              >
                + Wildfire Rail Block
              </button>
              <button
                onClick={() => triggerIncidentInject("SPACE")}
                className="btn btn-ghost"
                style={{ fontSize: "0.78rem", padding: "0.35rem 0.75rem" }}
              >
                + SAR Satellite Pass
              </button>
            </div>
          </div>

          {/* Incident Feed List */}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {incidents.map((inc) => (
              <div
                key={inc.id}
                style={{
                  background: "var(--panel-2)",
                  border:
                    inc.severity === "EMERGENCY"
                      ? "1px solid rgba(255, 0, 60, 0.5)"
                      : inc.severity === "CRITICAL"
                      ? "1px solid rgba(248, 113, 113, 0.3)"
                      : "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "0.9rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                  <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
                    <span
                      style={{
                        background:
                          inc.severity === "EMERGENCY"
                            ? "#ff003c"
                            : inc.severity === "CRITICAL"
                            ? "var(--danger)"
                            : inc.severity === "WARNING"
                            ? "var(--accent-3)"
                            : "var(--accent)",
                        color: "#fff",
                        fontFamily: "var(--mono)",
                        fontSize: "0.7rem",
                        fontWeight: 800,
                        padding: "0.1rem 0.4rem",
                        borderRadius: "3px",
                      }}
                    >
                      {inc.domain}
                    </span>
                    <strong style={{ fontSize: "0.92rem" }}>{inc.title}</strong>
                  </div>
                  <span style={{ fontFamily: "var(--mono)", fontSize: "0.75rem", color: "var(--muted)" }}>
                    {inc.time}
                  </span>
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
                  📍 {inc.location} • Threat Impact: {(inc.impactScore * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Panel: Game-Theoretic Wargame Solver */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.75rem",
          }}
        >
          <h2 style={{ fontSize: "1.25rem", marginBottom: "0.4rem" }}>
            ⚔️ Game-Theoretic Blockade &amp; Embargo Solver
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "1.2rem" }}>
            Evaluates 30 $\to$ 180 day adversarial pressure scenarios against Canadian defense supply chains.
          </p>

          <div style={{ marginBottom: "1rem" }}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Disruption Scenario:
            </label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.6rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
                fontSize: "0.85rem",
              }}
            >
              <option value="MARITIME_BLOCKADE">St. Lawrence Seaway / Atlantic Maritime Blockade</option>
              <option value="CRITICAL_MINERAL_EMBARGO">Foreign Critical Mineral Export Embargo</option>
              <option value="SCADA_CYBER_SABOTAGE">Trans-Canada Rail &amp; Port SCADA Sabotage</option>
              <option value="SUBSEA_CABLE_INTERDICTION">Atlantic Subsea Fiber Cable Interdiction</option>
              <option value="PERMAFROST_CORRIDOR_COLLAPSE">Hudson Bay Polar Railway Permafrost Collapse</option>
            </select>
          </div>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Adversary Pressure Level: <strong style={{ color: "var(--text)" }}>{(adversaryPressure * 100).toFixed(0)}%</strong>
            </label>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={adversaryPressure}
              onChange={(e) => setAdversaryPressure(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--danger)" }}
            />
          </div>

          {/* Strategic Option Output Box */}
          <div
            style={{
              background: "var(--panel-2)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              padding: "1.2rem",
            }}
          >
            <div style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--accent)", marginBottom: "0.4rem" }}>
              RECOMMENDED STRATEGIC OPTION TREE (SOT)
            </div>
            <strong style={{ fontSize: "0.98rem", color: "var(--text)" }}>
              Activate Defense Production Act (DPA) &amp; Churchill Polar Rail/Air Bridge
            </strong>
            <p style={{ fontSize: "0.82rem", color: "var(--muted)", margin: "0.5rem 0", lineHeight: 1.5 }}>
              Mandate direct allocation of domestic Class-1 Nickel, Cobalt, and Rare Earth stockpiles to NATO Tier-1
              primes while executing polar multi-modal rail freight bypass via Port of Churchill.
            </p>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", fontFamily: "var(--mono)" }}>
              <span style={{ color: "var(--accent-2)" }}>Readiness Gain: +38.5%</span>
              <span style={{ color: "var(--muted)" }}>Est. Cost: $45M CAD</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Footer */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/critical-minerals" className="btn btn-primary">
          Audit 31 Critical Minerals Stockpile →
        </Link>
        <Link href="/cluster-mesh" className="btn btn-ghost">
          Inspect Air-Gapped SCIF Cluster Mesh
        </Link>
        <Link href="/quantum-crypto" className="btn btn-ghost">
          Post-Quantum Cryptography &amp; ZKP
        </Link>
      </div>
    </div>
  );
}
