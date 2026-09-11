"use client";

import { useState } from "react";
import Link from "next/link";

interface ConnectorStream {
  id: string;
  name: string;
  protocol: string;
  category: "ERP" | "EDI" | "TELEMETRY" | "SCADA_OT";
  status: "ACTIVE_STREAMING" | "HEALTHY" | "LISTENING";
  eventsToday: string;
  latencyMs: number;
  description: string;
}

const CONNECTORS: ConnectorStream[] = [
  {
    id: "sap-s4hana",
    name: "SAP S/4HANA Materials Management",
    protocol: "OData v4 / IDoc RFC",
    category: "ERP",
    status: "ACTIVE_STREAMING",
    eventsToday: "4,821 Shipments",
    latencyMs: 42,
    description: "Automated ingestion of Bills of Lading, Purchase Orders, and multi-tier supplier nodes.",
  },
  {
    id: "edi-x12",
    name: "ANSI X12 EDI 204 / 214 / 315 Feeds",
    protocol: "AS2 / SFTP Secure Stream",
    category: "EDI",
    status: "HEALTHY",
    eventsToday: "1,290 Transactions",
    latencyMs: 18,
    description: "Motor carrier load tenders, shipment status notices, and ocean container departure events.",
  },
  {
    id: "ais-spire",
    name: "Spire Global / exactEarth AIS Stream",
    protocol: "WebSocket / NMEA AIVDM",
    category: "TELEMETRY",
    status: "ACTIVE_STREAMING",
    eventsToday: "28,400 Pings",
    latencyMs: 120,
    description: "Live vessel positions, speed over ground, GNSS spoofing anomaly detection, and dark fleet tagging.",
  },
  {
    id: "scada-opcua",
    name: "Industrial OT / Port Crane OPC UA",
    protocol: "OPC UA / MQTT Broker",
    category: "SCADA_OT",
    status: "ACTIVE_STREAMING",
    eventsToday: "142,000 PLC Tags",
    latencyMs: 8,
    description: "Port container crane availability, rail track interlocking switches, and pipeline pump pressure.",
  },
  {
    id: "noaa-swpc",
    name: "NOAA Space Weather Prediction Center",
    protocol: "REST / GeoJSON Alert",
    category: "TELEMETRY",
    status: "LISTENING",
    eventsToday: "48 Synoptic Alerts",
    latencyMs: 310,
    description: "Real-time solar geomagnetic Kp-index and high-latitude SATCOM degradation early warning.",
  },
  {
    id: "usgs-seismic",
    name: "USGS ShakeMap & Earthquake Hazards",
    protocol: "GeoJSON Event Feed",
    category: "TELEMETRY",
    status: "LISTENING",
    eventsToday: "14 Global Events",
    latencyMs: 280,
    description: "Automated corridor physical closure alerts triggered on seismic events exceeding magnitude 6.5.",
  },
];

export default function EnterpriseConnectorsPage() {
  const [activeCategory, setActiveCategory] = useState<string>("ALL");

  const filtered =
    activeCategory === "ALL"
      ? CONNECTORS
      : CONNECTORS.filter((c) => c.category === activeCategory);

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
                background: "rgba(168, 85, 247, 0.15)",
                color: "#c084fc",
                fontWeight: 700,
              }}
            >
              ZERO-TOUCH DATA PLANE
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
            Enterprise Connectors & Ingestion Pipeline
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
            Zero-touch automatic graph synthesis. Eliminates manual YAML authoring by listening continuously to enterprise
            ERP streams, EDI carrier transmissions, real-time AIS marine telemetry, and SCADA industrial historians.
          </p>
        </div>

        {/* Filter Badges */}
        <div style={{ display: "flex", gap: 8, marginBottom: 28 }}>
          {["ALL", "ERP", "EDI", "TELEMETRY", "SCADA_OT"].map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid",
                borderColor: activeCategory === cat ? "#c084fc" : "var(--border)",
                background: activeCategory === cat ? "rgba(168, 85, 247, 0.1)" : "var(--card-bg)",
                color: activeCategory === cat ? "#c084fc" : "var(--text-secondary)",
                fontSize: "0.85rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              {cat.replace(/_/g, " ")}
            </button>
          ))}
        </div>

        {/* Connectors Grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))",
            gap: 20,
            marginBottom: 40,
          }}
        >
          {filtered.map((conn) => (
            <div
              key={conn.id}
              style={{
                background: "var(--card-bg)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: 24,
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
                    {conn.protocol}
                  </span>
                  <h3 style={{ fontSize: "1.15rem", fontWeight: 700, margin: "6px 0 0", color: "var(--text-primary)" }}>
                    {conn.name}
                  </h3>
                </div>
                <span
                  style={{
                    padding: "3px 8px",
                    borderRadius: 4,
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    background: "rgba(34, 197, 94, 0.15)",
                    color: "#4ade80",
                    border: "1px solid rgba(34, 197, 94, 0.3)",
                  }}
                >
                  ● {conn.status}
                </span>
              </div>

              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", margin: "0 0 16px", lineHeight: 1.5 }}>
                {conn.description}
              </p>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 12,
                  padding: "10px 14px",
                  borderRadius: 8,
                  background: "rgba(0,0,0,0.25)",
                  fontSize: "0.8rem",
                }}
              >
                <div>
                  <div style={{ color: "var(--text-muted)", marginBottom: 2 }}>INGESTED TODAY</div>
                  <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>{conn.eventsToday}</div>
                </div>
                <div>
                  <div style={{ color: "var(--text-muted)", marginBottom: 2 }}>STREAM LATENCY</div>
                  <div style={{ fontWeight: 700, color: "#38bdf8" }}>{conn.latencyMs} ms</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Live Synthesis Demo Box */}
        <div
          style={{
            background: "var(--card-bg)",
            border: "1px solid rgba(192, 132, 252, 0.3)",
            borderRadius: 12,
            padding: 28,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div>
              <span style={{ fontSize: "0.8rem", color: "#c084fc", fontWeight: 700 }}>
                AUTOMATED GRAPH SYNTHESIZER
              </span>
              <h2 style={{ fontSize: "1.4rem", fontWeight: 800, margin: "4px 0 0", color: "var(--text-primary)" }}>
                Drop-in EDI 204 / 315 & Bill of Lading Synthesizer
              </h2>
            </div>
            <code style={{ fontSize: "0.85rem", color: "#c084fc" }}>
              continuity ingest-edi sample.edi
            </code>
          </div>
          <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", margin: 0, lineHeight: 1.6 }}>
            The <code>GraphSynthesizer</code> inspects all stop sequences, facility IDs, carrier SCACs, and cargo weights
            to automatically construct directed dependency edges with zero manual configuration.
          </p>
        </div>
      </div>
    </div>
  );
}
