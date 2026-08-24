"use client";

import { useState } from "react";
import Link from "next/link";

interface BOMItem {
  id: string;
  name: string;
  tier: number;
  supplier: string;
  country: string;
  singleSourced: boolean;
  leadTimeDays: number;
  bufferDays: number;
  criticality: number;
}

const SAMPLE_BOM: BOMItem[] = [
  {
    id: "COMP-T1-BATTERY",
    name: "Lithium-Ion Battery Pack Module (100 kWh)",
    tier: 1,
    supplier: "NextStar Energy (Windsor, ON)",
    country: "CAN",
    singleSourced: true,
    leadTimeDays: 21,
    bufferDays: 14,
    criticality: 0.95,
  },
  {
    id: "COMP-T2-CATHODE",
    name: "Nickel-Manganese-Cobalt (NMC 811) Cathode",
    tier: 2,
    supplier: "BASF Battery Materials (Bécancour, QC)",
    country: "CAN",
    singleSourced: false,
    leadTimeDays: 18,
    bufferDays: 20,
    criticality: 0.88,
  },
  {
    id: "COMP-T3-NICKEL",
    name: "Battery-Grade Class 1 Refined Nickel",
    tier: 3,
    supplier: "Vale Base Metals (Sudbury, ON)",
    country: "CAN",
    singleSourced: true,
    leadTimeDays: 30,
    bufferDays: 15,
    criticality: 0.92,
  },
  {
    id: "COMP-T3-LITHIUM",
    name: "Battery-Grade Lithium Hydroxide Monohydrate",
    tier: 3,
    supplier: "Nemaska Lithium (Whabouchi, QC)",
    country: "CAN",
    singleSourced: false,
    leadTimeDays: 25,
    bufferDays: 28,
    criticality: 0.85,
  },
];

export default function SupplyChainPage() {
  const [disruptionDays, setDisruptionDays] = useState<number>(7);
  const [dailyInvValue, setDailyInvValue] = useState<number>(5000000);
  const [vesselsDelayed, setVesselsDelayed] = useState<number>(2);
  const [dailyPlantBurn, setDailyPlantBurn] = useState<number>(150000);
  const [selectedTransport, setSelectedTransport] = useState<string>("balanced");

  // Economic calculations
  const dailyHolding = (dailyInvValue * 0.18) / 365.0;
  const dailyDemurrage = vesselsDelayed * 25000;
  const totalHolding = dailyHolding * disruptionDays;
  const totalDemurrage = dailyDemurrage * disruptionDays;
  const totalProductionLoss = dailyPlantBurn * disruptionDays;
  const totalLossCAD = totalHolding + totalDemurrage + totalProductionLoss;

  // Single sources & choke points
  const singleSources = SAMPLE_BOM.filter((b) => b.singleSourced);
  const exhaustedItems = SAMPLE_BOM.filter((b) => b.bufferDays <= disruptionDays);

  return (
    <div style={{ padding: "1.5rem 0" }}>
      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Enterprise &amp; Sovereign Resilience-as-Code</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Multi-Tier Supply Chain &amp; Economic Disruption Simulator
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Decompose multi-tier Bill of Materials (BOM) risks, pinpoint single-source supplier choke points,
          and calculate precise commercial losses from port demurrage, rail delays, and plant idling.
        </p>
      </header>

      {/* Top Level Summary Cards */}
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
          <div style={{ color: "var(--muted)", fontSize: "0.8rem", fontFamily: "var(--mono)" }}>
            ESTIMATED FINANCIAL LOSS
          </div>
          <div
            style={{
              fontSize: "1.8rem",
              fontWeight: 800,
              color: "var(--danger)",
              margin: "0.3rem 0",
            }}
          >
            CAD ${totalLossCAD.toLocaleString("en-CA", { maximumFractionDigits: 0 })}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>
            Over {disruptionDays} days disruption
          </div>
        </div>

        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.8rem", fontFamily: "var(--mono)" }}>
            BUFFER EXHAUSTED ITEMS
          </div>
          <div
            style={{
              fontSize: "1.8rem",
              fontWeight: 800,
              color: exhaustedItems.length > 0 ? "var(--accent-3)" : "var(--accent-2)",
              margin: "0.3rem 0",
            }}
          >
            {exhaustedItems.length} of {SAMPLE_BOM.length}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>
            Critical inventory stockout risk
          </div>
        </div>

        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.8rem", fontFamily: "var(--mono)" }}>
            SINGLE-SOURCE CHOKE POINTS
          </div>
          <div
            style={{
              fontSize: "1.8rem",
              fontWeight: 800,
              color: "var(--accent)",
              margin: "0.3rem 0",
            }}
          >
            {singleSources.length} Components
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>
            Zero immediate substitute available
          </div>
        </div>

        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border)",
            borderRadius: "8px",
            padding: "1.25rem",
          }}
        >
          <div style={{ color: "var(--muted)", fontSize: "0.8rem", fontFamily: "var(--mono)" }}>
            RECOMMENDED REROUTE
          </div>
          <div
            style={{
              fontSize: "1.3rem",
              fontWeight: 800,
              color: "var(--accent-2)",
              margin: "0.5rem 0",
            }}
          >
            CPKC Trans-Canada Rail
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>
            Cost: $348/ton • Transit: 96h
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        {/* Disruption Parameters Panel */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.5rem",
          }}
        >
          <h2 style={{ fontSize: "1.2rem", marginBottom: "1.2rem" }}>
            Disruption &amp; Cost Parameters
          </h2>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Disruption Duration: <strong style={{ color: "var(--text)" }}>{disruptionDays} Days</strong>
            </label>
            <input
              type="range"
              min="1"
              max="45"
              value={disruptionDays}
              onChange={(e) => setDisruptionDays(Number(e.target.value))}
              style={{ width: "100%", accentColor: "var(--accent)" }}
            />
          </div>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Daily In-Transit Inventory Value (CAD):
            </label>
            <input
              type="number"
              value={dailyInvValue}
              onChange={(e) => setDailyInvValue(Number(e.target.value))}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            />
          </div>

          <div style={{ marginBottom: "1.2rem" }}>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Delayed Vessels / Trains:
            </label>
            <input
              type="number"
              value={vesselsDelayed}
              onChange={(e) => setVesselsDelayed(Number(e.target.value))}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.4rem" }}>
              Daily Production Line Stoppage Burn (CAD):
            </label>
            <input
              type="number"
              value={dailyPlantBurn}
              onChange={(e) => setDailyPlantBurn(Number(e.target.value))}
              style={{
                width: "100%",
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                color: "var(--text)",
                padding: "0.5rem",
                borderRadius: "6px",
                fontFamily: "var(--mono)",
              }}
            />
          </div>
        </div>

        {/* Financial Loss Breakdown */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.5rem",
          }}
        >
          <h2 style={{ fontSize: "1.2rem", marginBottom: "1.2rem" }}>Financial Loss Breakdown</h2>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "0.8rem",
                background: "var(--panel-2)",
                borderRadius: "6px",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>Inventory Holding Cost</div>
                <div style={{ color: "var(--muted-2)", fontSize: "0.75rem" }}>18% annual carrying rate</div>
              </div>
              <div style={{ fontFamily: "var(--mono)", fontWeight: 700, color: "var(--text)" }}>
                CAD ${totalHolding.toLocaleString("en-CA", { maximumFractionDigits: 2 })}
              </div>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "0.8rem",
                background: "var(--panel-2)",
                borderRadius: "6px",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>Port Demurrage &amp; Detention</div>
                <div style={{ color: "var(--muted-2)", fontSize: "0.75rem" }}>
                  $25,000/vessel/day x {vesselsDelayed} vessels
                </div>
              </div>
              <div style={{ fontFamily: "var(--mono)", fontWeight: 700, color: "var(--text)" }}>
                CAD ${totalDemurrage.toLocaleString("en-CA", { maximumFractionDigits: 2 })}
              </div>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "0.8rem",
                background: "var(--panel-2)",
                borderRadius: "6px",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>Production Line Idling</div>
                <div style={{ color: "var(--muted-2)", fontSize: "0.75rem" }}>Gigafactory downtime costs</div>
              </div>
              <div style={{ fontFamily: "var(--mono)", fontWeight: 700, color: "var(--text)" }}>
                CAD ${totalProductionLoss.toLocaleString("en-CA", { maximumFractionDigits: 2 })}
              </div>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "1rem",
                background: "rgba(248, 113, 113, 0.1)",
                border: "1px solid rgba(248, 113, 113, 0.3)",
                borderRadius: "6px",
                marginTop: "0.5rem",
              }}
            >
              <strong style={{ color: "var(--danger)" }}>TOTAL ESTIMATED LOSS</strong>
              <strong style={{ fontFamily: "var(--mono)", fontSize: "1.1rem", color: "var(--danger)" }}>
                CAD ${totalLossCAD.toLocaleString("en-CA", { maximumFractionDigits: 2 })}
              </strong>
            </div>
          </div>
        </div>
      </div>

      {/* Multi-Tier BOM Table */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <h2 style={{ fontSize: "1.2rem", marginBottom: "1rem" }}>
          Multi-Tier Bill of Materials (BOM) Vulnerability Matrix
        </h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                <th style={{ padding: "0.6rem" }}>Tier</th>
                <th style={{ padding: "0.6rem" }}>Component / Material</th>
                <th style={{ padding: "0.6rem" }}>Supplier &amp; Location</th>
                <th style={{ padding: "0.6rem" }}>Sourcing</th>
                <th style={{ padding: "0.6rem" }}>Lead Time</th>
                <th style={{ padding: "0.6rem" }}>Buffer Days</th>
                <th style={{ padding: "0.6rem" }}>Disruption Impact</th>
              </tr>
            </thead>
            <tbody>
              {SAMPLE_BOM.map((item) => {
                const isExhausted = item.bufferDays <= disruptionDays;
                return (
                  <tr
                    key={item.id}
                    style={{
                      borderBottom: "1px solid var(--border)",
                      background: isExhausted ? "rgba(248, 113, 113, 0.05)" : "transparent",
                    }}
                  >
                    <td style={{ padding: "0.6rem", fontFamily: "var(--mono)" }}>
                      <span
                        style={{
                          background: item.tier === 1 ? "var(--accent)" : "var(--border-strong)",
                          color: "#000",
                          fontWeight: 700,
                          fontSize: "0.75rem",
                          padding: "0.15rem 0.4rem",
                          borderRadius: "3px",
                        }}
                      >
                        T{item.tier}
                      </span>
                    </td>
                    <td style={{ padding: "0.6rem", fontWeight: 600 }}>{item.name}</td>
                    <td style={{ padding: "0.6rem", color: "var(--muted)" }}>{item.supplier}</td>
                    <td style={{ padding: "0.6rem" }}>
                      {item.singleSourced ? (
                        <span style={{ color: "var(--danger)", fontWeight: 700, fontSize: "0.8rem" }}>
                          ⚠️ Single Sourced
                        </span>
                      ) : (
                        <span style={{ color: "var(--accent-2)", fontSize: "0.8rem" }}>Dual Sourced</span>
                      )}
                    </td>
                    <td style={{ padding: "0.6rem", fontFamily: "var(--mono)" }}>{item.leadTimeDays}d</td>
                    <td style={{ padding: "0.6rem", fontFamily: "var(--mono)" }}>{item.bufferDays}d</td>
                    <td style={{ padding: "0.6rem" }}>
                      {isExhausted ? (
                        <span
                          style={{
                            background: "rgba(248, 113, 113, 0.2)",
                            color: "var(--danger)",
                            padding: "0.2rem 0.5rem",
                            borderRadius: "4px",
                            fontWeight: 700,
                            fontSize: "0.75rem",
                          }}
                        >
                          EXHAUSTED ({item.bufferDays - disruptionDays}d margin)
                        </span>
                      ) : (
                        <span
                          style={{
                            background: "rgba(74, 222, 128, 0.15)",
                            color: "var(--accent-2)",
                            padding: "0.2rem 0.5rem",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                          }}
                        >
                          Protected (+{item.bufferDays - disruptionDays}d margin)
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/canadian-corridors" className="btn btn-primary">
          ← Back to Canadian Corridors
        </Link>
        <Link href="/sovereign-compliance" className="btn btn-ghost">
          Run Sovereign PBMM Audit →
        </Link>
      </div>
    </div>
  );
}
