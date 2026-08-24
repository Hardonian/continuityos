"use client";

import { useState } from "react";
import Link from "next/link";

interface MineralData {
  id: string;
  name: string;
  globalRank: number;
  refiningCap: number;
  natoDepScore: number;
  region: string;
  stockpileDays: number;
  substitute: string;
  tier: "CRITICAL_TIER_1" | "STRATEGIC_TIER_2";
}

const CRITICAL_MINERALS_LIST: MineralData[] = [
  {
    id: "NICKEL",
    name: "Class-1 Battery & Armor-Grade Nickel",
    globalRank: 5,
    refiningCap: 65.0,
    natoDepScore: 0.92,
    region: "Sudbury, ON & Voisey's Bay, NL",
    stockpileDays: 90,
    substitute: "None for high-temperature turbine alloys",
    tier: "CRITICAL_TIER_1",
  },
  {
    id: "LITHIUM",
    name: "Battery-Grade Lithium Hydroxide",
    globalRank: 6,
    refiningCap: 35.0,
    natoDepScore: 0.88,
    region: "James Bay, QC & Tanco, MB",
    stockpileDays: 60,
    substitute: "Sodium-ion (reduced energy density)",
    tier: "CRITICAL_TIER_1",
  },
  {
    id: "COBALT",
    name: "Refined Cobalt Cathode",
    globalRank: 4,
    refiningCap: 70.0,
    natoDepScore: 0.95,
    region: "Cobalt Camp & Port Colborne, ON",
    stockpileDays: 45,
    substitute: "LFP chemistries (cold-weather performance penalty)",
    tier: "CRITICAL_TIER_1",
  },
  {
    id: "RARE_EARTHS",
    name: "Heavy Rare Earth Elements (Nd, Pr, Dy, Tb)",
    globalRank: 7,
    refiningCap: 20.0,
    natoDepScore: 0.98,
    region: "Nechalacho, NWT & Strange Lake, QC",
    stockpileDays: 30,
    substitute: "Permanent magnet alternatives (-40% torque density)",
    tier: "CRITICAL_TIER_1",
  },
  {
    id: "CHROMITE",
    name: "High-Grade Ferrochrome",
    globalRank: 1,
    refiningCap: 15.0,
    natoDepScore: 0.94,
    region: "Ring of Fire, Northern ON",
    stockpileDays: 40,
    substitute: "None for ballistic armor plating",
    tier: "CRITICAL_TIER_1",
  },
  {
    id: "URANIUM",
    name: "Triuranium Octoxide (U3O8)",
    globalRank: 2,
    refiningCap: 95.0,
    natoDepScore: 0.90,
    region: "Athabasca Basin, SK",
    stockpileDays: 180,
    substitute: "Thorium breeder cycles (R&D only)",
    tier: "STRATEGIC_TIER_2",
  },
  {
    id: "TITANIUM",
    name: "Titanium Sponge & Ilmenite",
    globalRank: 3,
    refiningCap: 40.0,
    natoDepScore: 0.91,
    region: "Lac Tio, Havre-Saint-Pierre, QC",
    stockpileDays: 60,
    substitute: "Advanced carbon fiber composites",
    tier: "CRITICAL_TIER_1",
  },
  {
    id: "NIOBIUM",
    name: "Ferroniobium High-Strength Alloy",
    globalRank: 2,
    refiningCap: 85.0,
    natoDepScore: 0.86,
    region: "Niobec Mine, Saint-Honoré, QC",
    stockpileDays: 75,
    substitute: "Vanadium / Tantalum",
    tier: "STRATEGIC_TIER_2",
  },
];

export default function CriticalMineralsPage() {
  const [disruptionDays, setDisruptionDays] = useState<number>(45);

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">National Sovereign Critical Minerals &amp; Defense Assurance</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Canadian Critical Minerals &amp; NATO Stockpile Endurance Matrix
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Physics-based burn-rate and strategic reserve depletion models across Canada&apos;s 31 critical
          minerals, assessing domestic refining concentration and NATO Tier-1 defense aerospace dependencies.
        </p>
      </header>

      {/* Disruption Duration Slider Card */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.8rem" }}>
          <strong style={{ fontSize: "1.05rem" }}>⏱️ Disruption Time Horizon Simulation</strong>
          <span style={{ fontFamily: "var(--mono)", fontSize: "0.9rem", color: "var(--accent-3)", fontWeight: 700 }}>
            {disruptionDays} Days Disruption Horizon
          </span>
        </div>
        <input
          type="range"
          min="10"
          max="180"
          step="5"
          value={disruptionDays}
          onChange={(e) => setDisruptionDays(Number(e.target.value))}
          style={{ width: "100%", accentColor: "var(--accent-3)" }}
        />
      </div>

      {/* Grid of Minerals */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.2rem", marginBottom: "2rem" }}>
        {CRITICAL_MINERALS_LIST.map((m) => {
          const depletedPct = Math.min(100, Math.round((disruptionDays / m.stockpileDays) * 100));
          const isExhausted = depletedPct >= 95;
          const isWarning = depletedPct >= 70 && !isExhausted;

          return (
            <div
              key={m.id}
              style={{
                background: "var(--panel)",
                border: isExhausted
                  ? "1px solid rgba(255, 0, 60, 0.5)"
                  : isWarning
                  ? "1px solid rgba(251, 191, 36, 0.4)"
                  : "1px solid var(--border)",
                borderRadius: "10px",
                padding: "1.4rem",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem" }}>
                <strong style={{ fontSize: "1.05rem", color: "var(--text)" }}>{m.name}</strong>
                <span
                  style={{
                    background: isExhausted
                      ? "rgba(255, 0, 60, 0.15)"
                      : isWarning
                      ? "rgba(251, 191, 36, 0.15)"
                      : "rgba(74, 222, 128, 0.15)",
                    color: isExhausted ? "#ff4d6d" : isWarning ? "var(--accent-3)" : "var(--accent-2)",
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    fontFamily: "var(--mono)",
                    padding: "0.15rem 0.45rem",
                    borderRadius: "4px",
                  }}
                >
                  {isExhausted ? "STOCKPILE EXHAUSTED" : isWarning ? "DEPLETION WARNING" : "SUFFICIENT"}
                </span>
              </div>

              <div style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: "0.8rem" }}>
                📍 {m.region} • Global Rank: #{m.globalRank} • Domestic Refining: {m.refiningCap}%
              </div>

              {/* Depletion Progress Bar */}
              <div style={{ marginBottom: "0.8rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", fontFamily: "var(--mono)", marginBottom: "0.3rem" }}>
                  <span style={{ color: "var(--muted)" }}>Stockpile Depletion:</span>
                  <span style={{ color: isExhausted ? "var(--danger)" : "var(--text)", fontWeight: 700 }}>
                    {depletedPct}% (Baseline: {m.stockpileDays}d)
                  </span>
                </div>
                <div style={{ width: "100%", height: "6px", background: "var(--panel-2)", borderRadius: "3px", overflow: "hidden" }}>
                  <div
                    style={{
                      width: `${depletedPct}%`,
                      height: "100%",
                      background: isExhausted ? "#ff003c" : isWarning ? "var(--accent-3)" : "var(--accent)",
                      transition: "width 0.3s ease",
                    }}
                  />
                </div>
              </div>

              <div
                style={{
                  fontSize: "0.78rem",
                  color: "var(--muted)",
                  background: "var(--panel-2)",
                  padding: "0.5rem 0.7rem",
                  borderRadius: "6px",
                  borderLeft: "2px solid var(--accent)",
                }}
              >
                🔄 Substitute: {m.substitute}
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/war-room" className="btn btn-primary">
          ← Back to War Room
        </Link>
        <Link href="/cluster-mesh" className="btn btn-ghost">
          Inspect Air-Gapped SCIF Cluster Mesh →
        </Link>
      </div>
    </div>
  );
}
