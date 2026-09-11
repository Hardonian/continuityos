"use client";

import { useState } from "react";
import Link from "next/link";

interface GlobalCorridor {
  id: string;
  name: string;
  category: "MARITIME_CHOKEPOINT" | "INLAND_WATERWAY" | "STRATEGIC_MINERALS" | "ENERGY_CANAL";
  region: string;
  annualTonnage: string;
  threat: string;
  nominalDays: number;
  alternateRoute: string;
  alternateDays: number;
  rating: "AAA" | "AA" | "A" | "BBB" | "BB";
  status: "OPEN" | "OPEN_DEGRADED" | "OPEN_BUT_UNINSURABLE" | "OPEN_BUT_NAVIGATION_UNTRUSTED";
}

const GLOBAL_CORRIDORS: GlobalCorridor[] = [
  {
    id: "malacca-strait",
    name: "Strait of Malacca",
    category: "MARITIME_CHOKEPOINT",
    region: "Southeast Asia",
    annualTonnage: "1,200 Million Tonnes",
    threat: "Extreme traffic congestion, pirate littoral chokepoints, naval interdiction",
    nominalDays: 3.0,
    alternateRoute: "Sunda / Lombok Deepwater Bypass",
    alternateDays: 6.5,
    rating: "A",
    status: "OPEN",
  },
  {
    id: "suez-red-sea",
    name: "Suez Canal & Bab-el-Mandeb",
    category: "MARITIME_CHOKEPOINT",
    region: "Middle East / Red Sea",
    annualTonnage: "1,000 Million Tonnes",
    threat: "Anti-ship drone/missile attacks & Lloyd's War-Risk underwriter cancellation",
    nominalDays: 4.0,
    alternateRoute: "Cape of Good Hope Circumnavigation",
    alternateDays: 16.0,
    rating: "BBB",
    status: "OPEN_BUT_UNINSURABLE",
  },
  {
    id: "panama-canal",
    name: "Panama Canal Locks",
    category: "MARITIME_CHOKEPOINT",
    region: "Central America",
    annualTonnage: "510 Million Tonnes",
    threat: "Gatun Lake freshwater drought restrictions & vessel draft limits (<44 ft)",
    nominalDays: 2.0,
    alternateRoute: "US Intermodal Rail Landbridge (LA/Long Beach -> Houston)",
    alternateDays: 7.0,
    rating: "A",
    status: "OPEN",
  },
  {
    id: "hormuz-strait",
    name: "Strait of Hormuz",
    category: "ENERGY_CANAL",
    region: "Persian Gulf",
    annualTonnage: "950 Million Tonnes",
    threat: "Petroleum tanker seizures, naval mine warfare & GNSS spoofing floods",
    nominalDays: 2.0,
    alternateRoute: "Saudi East-West Crude Pipeline (Petroline to Yanbu)",
    alternateDays: 5.0,
    rating: "BBB",
    status: "OPEN_BUT_NAVIGATION_UNTRUSTED",
  },
  {
    id: "taiwan-strait",
    name: "Taiwan Strait Advanced Semiconductor Corridor",
    category: "STRATEGIC_MINERALS",
    region: "East Asia",
    annualTonnage: "750 Million Tonnes",
    threat: "Airspace denial, naval blockade cordons & advanced foundry logistics severance",
    nominalDays: 3.0,
    alternateRoute: "Luzon Strait / East Philippine Sea Maritime Bypass",
    alternateDays: 5.5,
    rating: "BB",
    status: "OPEN_DEGRADED",
  },
  {
    id: "baltic-danish-straits",
    name: "Baltic Sea & Danish Straits",
    category: "MARITIME_CHOKEPOINT",
    region: "Northern Europe",
    annualTonnage: "420 Million Tonnes",
    threat: "Subsea communications cable cutting, dark fleet collisions, GPS jamming",
    nominalDays: 3.0,
    alternateRoute: "Kiel Canal / North German Heavy Rail Transit",
    alternateDays: 4.5,
    rating: "AA",
    status: "OPEN",
  },
  {
    id: "rhine-alpine",
    name: "Rhine-Alpine Inland Freight Corridor",
    category: "INLAND_WATERWAY",
    region: "Western Europe",
    annualTonnage: "300 Million Tonnes",
    threat: "Kaub Gauge low-water drought barge strandings & Rhine rail congestion",
    nominalDays: 4.0,
    alternateRoute: "Betuwe Line Dedicated Heavy Freight Rail (Rotterdam -> Ruhr)",
    alternateDays: 3.5,
    rating: "AA",
    status: "OPEN",
  },
  {
    id: "arctic-northwest-passage",
    name: "Canadian Arctic Northwest Passage & Ring of Fire",
    category: "STRATEGIC_MINERALS",
    region: "North America (Arctic)",
    annualTonnage: "45 Million Tonnes",
    threat: "Multi-year pack ice obstruction, polar geomagnetic blackout & zero LEO SATCOM",
    nominalDays: 18.0,
    alternateRoute: "Trans-Canada All-Weather Rail Corridor (CN/CPKC)",
    alternateDays: 8.0,
    rating: "A",
    status: "OPEN",
  },
];

export default function CorridorHubPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [activeCorridor, setActiveCorridor] = useState<GlobalCorridor | null>(GLOBAL_CORRIDORS[0]);

  const filtered =
    selectedCategory === "ALL"
      ? GLOBAL_CORRIDORS
      : GLOBAL_CORRIDORS.filter((c) => c.category === selectedCategory);

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
                background: "rgba(56, 189, 248, 0.15)",
                color: "#38bdf8",
                fontWeight: 700,
              }}
            >
              GLOBAL CORRIDOR HUB
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
            Global Strategic Chokepoint Catalog
          </h1>
          <p
            style={{
              fontSize: "1rem",
              color: "var(--text-muted)",
              marginTop: 8,
              maxWidth: 800,
              lineHeight: 1.6,
            }}
          >
            Pre-modeled, crowd-verified topological dependency graphs for the eight critical maritime, energy,
            and critical mineral chokepoints governing 85% of global commerce and Allied defense logistics.
          </p>
        </div>

        {/* Category Filters */}
        <div style={{ display: "flex", gap: 8, marginBottom: 28, flexWrap: "wrap" }}>
          {["ALL", "MARITIME_CHOKEPOINT", "ENERGY_CANAL", "STRATEGIC_MINERALS", "INLAND_WATERWAY"].map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid",
                borderColor: selectedCategory === cat ? "#38bdf8" : "var(--border)",
                background: selectedCategory === cat ? "rgba(56, 189, 248, 0.1)" : "var(--card-bg)",
                color: selectedCategory === cat ? "#38bdf8" : "var(--text-secondary)",
                fontSize: "0.85rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {cat.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {/* Grid of Corridors */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
            gap: 20,
            marginBottom: 40,
          }}
        >
          {filtered.map((corridor) => {
            const isSelected = activeCorridor?.id === corridor.id;
            return (
              <div
                key={corridor.id}
                onClick={() => setActiveCorridor(corridor)}
                style={{
                  background: "var(--card-bg)",
                  border: "1px solid",
                  borderColor: isSelected ? "#38bdf8" : "var(--border)",
                  borderRadius: 12,
                  padding: 24,
                  cursor: "pointer",
                  transition: "all 0.2s ease",
                  boxShadow: isSelected ? "0 0 20px rgba(56, 189, 248, 0.2)" : "none",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <div>
                    <span
                      style={{
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: 4,
                        background: "rgba(255, 255, 255, 0.08)",
                        color: "var(--text-muted)",
                      }}
                    >
                      {corridor.region}
                    </span>
                    <h3 style={{ fontSize: "1.2rem", fontWeight: 700, margin: "6px 0 0", color: "var(--text-primary)" }}>
                      {corridor.name}
                    </h3>
                  </div>
                  <div
                    style={{
                      padding: "4px 10px",
                      borderRadius: 6,
                      fontSize: "0.85rem",
                      fontWeight: 800,
                      background:
                        corridor.rating.startsWith("A")
                          ? "rgba(34, 197, 94, 0.15)"
                          : "rgba(234, 179, 8, 0.15)",
                      color: corridor.rating.startsWith("A") ? "#4ade80" : "#facc15",
                      border: "1px solid",
                      borderColor: corridor.rating.startsWith("A") ? "#22c55e" : "#eab308",
                    }}
                  >
                    GRADE {corridor.rating}
                  </div>
                </div>

                <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: "0 0 16px", lineHeight: 1.5 }}>
                  {corridor.threat}
                </p>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr",
                    gap: 12,
                    padding: "12px 14px",
                    borderRadius: 8,
                    background: "rgba(0,0,0,0.25)",
                    fontSize: "0.8rem",
                  }}
                >
                  <div>
                    <div style={{ color: "var(--text-muted)", marginBottom: 2 }}>ANNUAL TONNAGE</div>
                    <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>{corridor.annualTonnage}</div>
                  </div>
                  <div>
                    <div style={{ color: "var(--text-muted)", marginBottom: 2 }}>NOMINAL TRANSIT</div>
                    <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>{corridor.nominalDays} Days</div>
                  </div>
                </div>

                <div style={{ marginTop: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: corridor.status === "OPEN" ? "#4ade80" : "#fbbf24",
                    }}
                  >
                    ● {corridor.status.replace(/_/g, " ")}
                  </span>
                  <code style={{ fontSize: "0.75rem", color: "#38bdf8" }}>
                    continuity hub pull {corridor.id}
                  </code>
                </div>
              </div>
            );
          })}
        </div>

        {/* Active Corridor Inspection Banner */}
        {activeCorridor && (
          <div
            style={{
              background: "var(--card-bg)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              borderRadius: 12,
              padding: 28,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <div>
                <span style={{ fontSize: "0.8rem", color: "#38bdf8", fontWeight: 700 }}>
                  TOPOLOGY RECONCILIATION & ROUTE SUBSTITUTION
                </span>
                <h2 style={{ fontSize: "1.5rem", fontWeight: 800, margin: "4px 0 0", color: "var(--text-primary)" }}>
                  {activeCorridor.name}
                </h2>
              </div>
              <Link
                href="/insurance-underwriting"
                style={{
                  padding: "10px 18px",
                  borderRadius: 6,
                  background: "#38bdf8",
                  color: "#000",
                  fontWeight: 700,
                  fontSize: "0.85rem",
                  textDecoration: "none",
                }}
              >
                Assess War-Risk Discount →
              </Link>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-secondary)", marginBottom: 8 }}>
                  PRIMARY OPERATIONAL RISK
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6 }}>
                  {activeCorridor.threat}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--text-secondary)", marginBottom: 8 }}>
                  VERIFIED ADVISORY ALTERNATE PATH
                </div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6 }}>
                  <strong>{activeCorridor.alternateRoute}</strong> ({activeCorridor.alternateDays} days transit, delta: +
                  {(activeCorridor.alternateDays - activeCorridor.nominalDays).toFixed(1)}d).
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
