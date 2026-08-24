"use client";

import { useState } from "react";
import Link from "next/link";

interface CorridorNode {
  id: string;
  name: string;
  type: string;
  location: string;
  metric: string;
  status: "NOMINAL" | "DEGRADED" | "CRITICAL";
}

interface CorridorData {
  id: string;
  title: string;
  category: string;
  sovereignPriority: string;
  clearance: string;
  continuityScore: number;
  activeRisk: number;
  nodes: CorridorNode[];
  modes: string[];
  summary: string;
}

const CORRIDORS: CorridorData[] = [
  {
    id: "critical-minerals",
    title: "Ontario Ring of Fire to Windsor EV Gigafactory Corridor",
    category: "Strategic Critical Minerals",
    sovereignPriority: "National Priority Tier-1 (NRCan)",
    clearance: "PROTECTED_B // CANADIAN EYES ONLY",
    continuityScore: 0.96,
    activeRisk: 0.04,
    modes: ["Rail (CN/CPKC)", "Long-Haul Heavy Haulage", "Great Lakes Maritime"],
    summary:
      "Strategic nickel, cobalt, and lithium supply chain feeding Canada's automotive EV gigafactories and aerospace defense alloys.",
    nodes: [
      {
        id: "ROF-MINE-01",
        name: "James Bay Ring of Fire Extraction Hub",
        type: "Mine & Refinery",
        location: "52.9°N, 86.1°W",
        metric: "Stockpile: 45 Days Reserve",
        status: "NOMINAL",
      },
      {
        id: "SUDBURY-SMELT",
        name: "Sudbury Smelting & Refining Complex",
        type: "Processing Hub",
        location: "46.5°N, 80.9°W",
        metric: "Utilization: 94% Capacity",
        status: "NOMINAL",
      },
      {
        id: "WINDSOR-GIGA",
        name: "Windsor NextStar EV Battery Gigafactory",
        type: "Manufacturing Plant",
        location: "42.3°N, 83.0°W",
        metric: "Daily Demand: 125 MWh",
        status: "NOMINAL",
      },
      {
        id: "MTL-PORT-EXP",
        name: "Port of Montreal Transatlantic Terminal",
        type: "Maritime Port",
        location: "45.5°N, 73.5°W",
        metric: "Container Dwell: 2.1 Days",
        status: "NOMINAL",
      },
    ],
  },
  {
    id: "arctic-norad",
    title: "Canadian Arctic Sovereignty & NORAD Northern Defense Corridor",
    category: "Arctic Defense & Northern Logistics",
    sovereignPriority: "National Defense (DND/CAF / NORAD)",
    clearance: "SECRET // REL_TO_CAN",
    continuityScore: 0.89,
    activeRisk: 0.11,
    modes: ["CCG Icebreaker Escort", "Heavy Airlift (CC-177)", "Arctic Sealift"],
    summary:
      "Essential Arctic sovereignty resupply linking CFS Alert, Nanisivik naval transition infrastructure, and the Port of Churchill deepwater gateway.",
    nodes: [
      {
        id: "CFS-ALERT",
        name: "Canadian Forces Station Alert",
        type: "Defense SIGINT Facility",
        location: "82.5°N, 62.3°W",
        metric: "Diesel Buffer: 120 Days",
        status: "NOMINAL",
      },
      {
        id: "NANISIVIK-HUB",
        name: "Nanisivik Naval Transition Facility",
        type: "Maritime Refueling Hub",
        location: "73.0°N, 84.5°W",
        metric: "Ice Thickness: 1.4m (Navigable)",
        status: "DEGRADED",
      },
      {
        id: "CHURCHILL-PORT",
        name: "Port of Churchill Arctic Deepwater Port",
        type: "Deepwater Rail Gateway",
        location: "58.7°N, 94.2°W",
        metric: "Draft Available: 11.5m",
        status: "NOMINAL",
      },
      {
        id: "IQALUIT-FOL",
        name: "Iqaluit Forward Operating Location (FOL)",
        type: "Tactical Airfield",
        location: "63.7°N, 68.5°W",
        metric: "Runway Status: 100% Operational",
        status: "NOMINAL",
      },
    ],
  },
  {
    id: "trans-canada-rail",
    title: "Trans-Canada CPKC & CN Intermodal Freight Corridor",
    category: "Intermodal Container & Freight Logistics",
    sovereignPriority: "National Commerce (Transport Canada)",
    clearance: "PROTECTED_A // COMMERCIAL",
    continuityScore: 0.94,
    activeRisk: 0.06,
    modes: ["CPKC Transcontinental", "CN Intermodal Rail", "Highway 1 Logistics"],
    summary:
      "Canada's commercial backbone connecting the Port of Vancouver and Prince Rupert to Calgary, Toronto, Montreal, and Halifax gateways.",
    nodes: [
      {
        id: "VAN-PORT",
        name: "Port of Vancouver (Roberts Bank)",
        type: "Asia-Pacific Port",
        location: "49.3°N, 123.1°W",
        metric: "Throughput: 3.8M TEU/yr",
        status: "NOMINAL",
      },
      {
        id: "PR-PORT",
        name: "Port of Prince Rupert Fairview",
        type: "Northern Pacific Port",
        location: "54.3°N, 130.3°W",
        metric: "Rail Fluidity: High",
        status: "NOMINAL",
      },
      {
        id: "CALGARY-YARD",
        name: "Calgary CPKC Intermodal Logistics Park",
        type: "Inland Rail Terminal",
        location: "51.0°N, 114.0°W",
        metric: "Yard Dwell: 18.5h",
        status: "NOMINAL",
      },
      {
        id: "TORONTO-HUB",
        name: "Toronto / Brampton Intermodal Hub",
        type: "Intermodal Freight Terminal",
        location: "43.7°N, 79.5°W",
        metric: "Chassis Availability: 92%",
        status: "NOMINAL",
      },
    ],
  },
  {
    id: "st-lawrence-seaway",
    title: "St. Lawrence Seaway & Great Lakes Bulk Lock Corridor",
    category: "Maritime Bulk Commodities",
    sovereignPriority: "Strategic Agri-Food & Steel Export",
    clearance: "PROTECTED_A // COMMERCIAL",
    continuityScore: 0.92,
    activeRisk: 0.08,
    modes: ["Great Lakes Bulk Carrier", "St. Lawrence Locks", "Short-Sea Shipping"],
    summary:
      "Critical deep-draft maritime gateway handling agricultural grain, iron ore, and specialized manufacturing freight across Ontario and Quebec.",
    nodes: [
      {
        id: "WELLAND-LOCK8",
        name: "Welland Canal Flight Locks (Lock 8)",
        type: "Seaway Lock System",
        location: "42.9°N, 79.2°W",
        metric: "Transit Draft: 8.08m Max",
        status: "NOMINAL",
      },
      {
        id: "MLO-LOCKS",
        name: "Montreal-Lake Ontario (MLO) Lock System",
        type: "Descent Lock Control",
        location: "45.4°N, 73.6°W",
        metric: "Water Level: +0.42m vs Datum",
        status: "NOMINAL",
      },
      {
        id: "MTL-GRAIN",
        name: "Port of Montreal Grain Elevator Complex",
        type: "Bulk Export Terminal",
        location: "45.5°N, 73.5°W",
        metric: "Grain Stockpile: 30 Days",
        status: "NOMINAL",
      },
      {
        id: "QUEBEC-PORT",
        name: "Port of Québec Deepwater Transshipment",
        type: "Deep-Draft Harbor",
        location: "46.8°N, 71.2°W",
        metric: "Berth Occupancy: 68%",
        status: "NOMINAL",
      },
    ],
  },
];

export default function CanadianCorridorsPage() {
  const [selectedId, setSelectedId] = useState<string>("critical-minerals");
  const [disruptionDays, setDisruptionDays] = useState<number>(0);

  const active = CORRIDORS.find((c) => c.id === selectedId) || CORRIDORS[0];

  // Dynamic calculated continuity under disruption slider
  const simulatedContinuity = Math.max(
    0.4,
    Math.round((active.continuityScore - disruptionDays * 0.035) * 100) / 100
  );
  const simulatedRisk = Math.round((1.0 - simulatedContinuity) * 100) / 100;

  return (
    <div style={{ padding: "1.5rem 0" }}>
      {/* Classification Marking Header */}
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
        🇨🇦 CANADIAN NATIONAL SOVEREIGN ENCLAVE // {active.clearance}
      </div>

      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">National Resilience &amp; Critical Infrastructure</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Canadian Sovereign Supply Corridors
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Real-time cyber-physical continuity assurance for Canadian strategic minerals,
          Arctic defense corridors, transcontinental intermodal freight, and the Great Lakes Seaway.
        </p>
      </header>

      {/* Corridor Selector Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "1rem",
          marginBottom: "2rem",
        }}
      >
        {CORRIDORS.map((c) => {
          const isSelected = c.id === selectedId;
          return (
            <button
              key={c.id}
              onClick={() => setSelectedId(c.id)}
              style={{
                background: isSelected ? "var(--panel-2)" : "var(--panel)",
                border: isSelected ? "2px solid var(--accent)" : "1px solid var(--border)",
                borderRadius: "8px",
                padding: "1rem",
                textAlign: "left",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              <div
                style={{
                  color: isSelected ? "var(--accent)" : "var(--muted)",
                  fontSize: "0.75rem",
                  fontFamily: "var(--mono)",
                  fontWeight: 600,
                  textTransform: "uppercase",
                  marginBottom: "0.3rem",
                }}
              >
                {c.category}
              </div>
              <div style={{ color: "var(--text)", fontWeight: 700, fontSize: "0.95rem" }}>
                {c.title.split(" Corridor")[0]}
              </div>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: "0.8rem",
                  fontSize: "0.82rem",
                }}
              >
                <span style={{ color: "var(--muted)" }}>Continuity:</span>
                <strong style={{ color: "var(--accent-2)" }}>
                  {(c.continuityScore * 100).toFixed(0)}%
                </strong>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Corridor Command Panel */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.75rem",
          marginBottom: "2rem",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            flexWrap: "wrap",
            gap: "1rem",
            borderBottom: "1px solid var(--border)",
            paddingBottom: "1.25rem",
            marginBottom: "1.5rem",
          }}
        >
          <div>
            <span
              style={{
                background: "rgba(56, 189, 248, 0.15)",
                color: "var(--accent)",
                padding: "0.2rem 0.6rem",
                borderRadius: "4px",
                fontFamily: "var(--mono)",
                fontSize: "0.8rem",
                fontWeight: 600,
              }}
            >
              {active.sovereignPriority}
            </span>
            <h2 style={{ fontSize: "1.5rem", margin: "0.5rem 0 0.2rem 0" }}>{active.title}</h2>
            <p style={{ color: "var(--muted)", fontSize: "0.95rem", maxWidth: "700px" }}>
              {active.summary}
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: "1.5rem",
              background: "var(--panel-2)",
              padding: "1rem 1.5rem",
              borderRadius: "8px",
              border: "1px solid var(--border)",
            }}
          >
            <div>
              <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
                CONTINUITY
              </div>
              <div
                style={{
                  fontSize: "1.6rem",
                  fontWeight: 800,
                  color: simulatedContinuity > 0.85 ? "var(--accent-2)" : "var(--accent-3)",
                }}
              >
                {(simulatedContinuity * 100).toFixed(0)}%
              </div>
            </div>
            <div style={{ borderLeft: "1px solid var(--border)", paddingLeft: "1.5rem" }}>
              <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
                ACTIVE RISK
              </div>
              <div
                style={{
                  fontSize: "1.6rem",
                  fontWeight: 800,
                  color: simulatedRisk < 0.2 ? "var(--accent)" : "var(--danger)",
                }}
              >
                {(simulatedRisk * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>

        {/* Live Disruption Simulator Slider */}
        <div
          style={{
            background: "rgba(251, 191, 36, 0.05)",
            border: "1px solid rgba(251, 191, 36, 0.2)",
            borderRadius: "8px",
            padding: "1.25rem",
            marginBottom: "1.75rem",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "0.5rem",
            }}
          >
            <label
              htmlFor="disruption-slider"
              style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text)" }}
            >
              Simulate Severe Disruption Shock:{" "}
              <span style={{ color: "var(--accent-3)", fontFamily: "var(--mono)" }}>
                +{disruptionDays} Days Stoppage
              </span>
            </label>
            <button
              onClick={() => setDisruptionDays(0)}
              style={{
                background: "transparent",
                border: "1px solid var(--border)",
                color: "var(--muted)",
                padding: "0.2rem 0.5rem",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "0.8rem",
              }}
            >
              Reset to Baseline
            </button>
          </div>
          <input
            id="disruption-slider"
            type="range"
            min="0"
            max="30"
            value={disruptionDays}
            onChange={(e) => setDisruptionDays(Number(e.target.value))}
            style={{ width: "100%", accentColor: "var(--accent-3)", cursor: "pointer" }}
          />
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              color: "var(--muted)",
              fontSize: "0.75rem",
              marginTop: "0.3rem",
              fontFamily: "var(--mono)",
            }}
          >
            <span>0d (Nominal Operations)</span>
            <span>15d (Moderate Cascade)</span>
            <span>30d (Severe Disruption)</span>
          </div>
        </div>

        {/* Critical Nodes Topology */}
        <h3 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Strategic Node Status &amp; Telemetry</h3>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "1rem",
            marginBottom: "1.5rem",
          }}
        >
          {active.nodes.map((node) => (
            <div
              key={node.id}
              style={{
                background: "var(--panel-2)",
                border: "1px solid var(--border)",
                borderRadius: "8px",
                padding: "1rem",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "0.4rem",
                }}
              >
                <span style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--muted)" }}>
                  {node.type}
                </span>
                <span
                  style={{
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    padding: "0.15rem 0.4rem",
                    borderRadius: "4px",
                    background:
                      node.status === "NOMINAL"
                        ? "rgba(74, 222, 128, 0.15)"
                        : "rgba(251, 191, 36, 0.15)",
                    color: node.status === "NOMINAL" ? "var(--accent-2)" : "var(--accent-3)",
                  }}
                >
                  {node.status}
                </span>
              </div>
              <div style={{ fontWeight: 700, fontSize: "0.95rem", color: "var(--text)" }}>
                {node.name}
              </div>
              <div style={{ color: "var(--muted-2)", fontSize: "0.8rem", marginTop: "0.3rem" }}>
                📍 {node.location}
              </div>
              <div
                style={{
                  marginTop: "0.6rem",
                  paddingTop: "0.6rem",
                  borderTop: "1px solid var(--border)",
                  fontSize: "0.82rem",
                  color: "var(--accent)",
                  fontFamily: "var(--mono)",
                }}
              >
                {node.metric}
              </div>
            </div>
          ))}
        </div>

        {/* Multi-modal Rerouting Directive */}
        <div
          style={{
            background: "rgba(56, 189, 248, 0.04)",
            border: "1px solid rgba(56, 189, 248, 0.2)",
            borderRadius: "8px",
            padding: "1rem 1.25rem",
          }}
        >
          <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--accent)" }}>
            🛡️ Advisory Multi-Modal Continuity Directive
          </div>
          <p style={{ fontSize: "0.9rem", color: "var(--muted)", margin: "0.3rem 0 0 0" }}>
            Active freight modes: {active.modes.join(" • ")}. In the event of primary corridor degradation,
            the deterministic solver dynamically prioritizes rail bypass corridors and secondary maritime draft channels.
          </p>
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/supply-chain" className="btn btn-primary">
          Simulate Multi-Tier Supply Chain BOM →
        </Link>
        <Link href="/rfp-proposal" className="btn btn-ghost">
          Inspect Government RFP &amp; PBMM Pack
        </Link>
      </div>
    </div>
  );
}
