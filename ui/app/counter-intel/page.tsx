"use client";

import { useState } from "react";
import Link from "next/link";

interface DarkContact {
  id: string;
  lat: number;
  lon: number;
  speed: number;
  aisStatus: "ACTIVE" | "DARK_UNVERIFIED" | "SPOOFED_MMSI";
  distanceKm: number;
  threatScore: number;
  anomalies: string[];
}

interface SatellitePass {
  id: string;
  satellite: string;
  sensor: "SAR_RADAR" | "OPTICAL_HIGH_RES" | "SIGINT_ELINT";
  elevationDeg: number;
  durationMins: number;
  exposureScore: number;
  maskingDirective: string;
}

const SAMPLE_DARK_CONTACTS: DarkContact[] = [
  {
    id: "RADAR-TGT-081",
    lat: 48.42,
    lon: -64.55,
    speed: 1.4,
    aisStatus: "DARK_UNVERIFIED",
    distanceKm: 8.2,
    threatScore: 0.88,
    anomalies: ["AIS Transponder Inactive", "Chokepoint Loitering (1.4 kts)", "Subsea Cable Proximity"],
  },
  {
    id: "RADAR-TGT-094",
    lat: 48.15,
    lon: -65.10,
    speed: 13.8,
    aisStatus: "ACTIVE",
    distanceKm: 28.5,
    threatScore: 0.15,
    anomalies: ["Commercial Container Cargo (Nominal Transit)"],
  },
  {
    id: "RADAR-TGT-112",
    lat: 47.95,
    lon: -63.80,
    speed: 0.6,
    aisStatus: "SPOOFED_MMSI",
    distanceKm: 14.1,
    threatScore: 0.76,
    anomalies: ["MMSI Kinematic Mismatch", "Ghost Transponder Cluster"],
  },
];

const SAMPLE_SATELLITE_PASSES: SatellitePass[] = [
  {
    id: "PASS-SAR-01",
    satellite: "COSMO-SkyMed 4 (Synthetic Aperture Radar)",
    sensor: "SAR_RADAR",
    elevationDeg: 68.5,
    durationMins: 11,
    exposureScore: 0.82,
    maskingDirective: "Execute RF cutoff & scatter decoy transponders during orbital pass window",
  },
  {
    id: "PASS-OPT-02",
    satellite: "Gaofen-3 Polar SAR Constellation",
    sensor: "SAR_RADAR",
    elevationDeg: 54.2,
    durationMins: 9,
    exposureScore: 0.65,
    maskingDirective: "Directional low-power LPI communications only; shroud metallic convoys",
  },
  {
    id: "PASS-SIG-03",
    satellite: "Resurs-P High-Resolution Reconnaissance",
    sensor: "OPTICAL_HIGH_RES",
    elevationDeg: 41.0,
    durationMins: 8,
    exposureScore: 0.42,
    maskingDirective: "Standard cloud cover thermal dispersion active",
  },
];

export default function CounterIntelPage() {
  const [emconLevel, setEmconLevel] = useState<"ALPHA" | "BRAVO" | "CHARLIE">("BRAVO");
  const [selectedAsset, setSelectedAsset] = useState<string>("HALIFAX-CABLE-ZONE");

  const darkCount = SAMPLE_DARK_CONTACTS.filter((c) => c.aisStatus !== "ACTIVE").length;
  const maxThreat = Math.max(...SAMPLE_DARK_CONTACTS.map((c) => c.threatScore));
  const peakExposure = Math.max(...SAMPLE_SATELLITE_PASSES.map((p) => p.exposureScore));

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
        🛡️ SOVEREIGN COUNTER-INTELLIGENCE &amp; SURVEILLANCE RESILIENCE // SECRET // CANADIAN EYES ONLY
      </div>

      <header style={{ marginBottom: "2rem" }}>
        <p className="eyebrow">Multi-Domain Anti-Reconnaissance &amp; Threat Detection</p>
        <h1 style={{ fontSize: "2.2rem", fontWeight: 800, margin: "0.2rem 0" }}>
          Counter-Intelligence &amp; Tactical EMCON HUD
        </h1>
        <p className="lede" style={{ maxWidth: "880px" }}>
          Defensive anti-reconnaissance engine correlating non-transmitting (dark) maritime fleet activity,
          predicting foreign orbital SAR / Earth Observation satellite passes, and managing convoy emission
          control (EMCON) posture.
        </p>
      </header>

      {/* Top Status Cards */}
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
            DARK FLEET CONTACTS
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--danger)", margin: "0.3rem 0" }}>
            {darkCount} Unverified
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>Within 30km sensor perimeter</div>
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
            ORBITAL SAR EXPOSURE
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--accent-3)", margin: "0.3rem 0" }}>
            {(peakExposure * 100).toFixed(0)}% Index
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>3 foreign overflight passes</div>
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
            EMCON POSTURE
          </div>
          <div
            style={{
              fontSize: "1.6rem",
              fontWeight: 800,
              color: emconLevel === "ALPHA" ? "var(--danger)" : "var(--accent)",
              margin: "0.3rem 0",
            }}
          >
            LEVEL {emconLevel}
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>
            {emconLevel === "ALPHA"
              ? "Emission Silence (Silent Mode)"
              : emconLevel === "BRAVO"
              ? "Directional LPI Communications"
              : "Standard Active Transmissions"}
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
          <div style={{ color: "var(--muted)", fontSize: "0.75rem", fontFamily: "var(--mono)" }}>
            PEAK THREAT SCORE
          </div>
          <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "var(--danger)", margin: "0.3rem 0" }}>
            {(maxThreat * 100).toFixed(0)}% Risk
          </div>
          <div style={{ fontSize: "0.8rem", color: "var(--muted-2)" }}>Active loitering anomaly</div>
        </div>
      </div>

      {/* EMCON Posture Selector Bar */}
      <div
        style={{
          background: "var(--panel)",
          border: "1px solid var(--border-strong)",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
          <h2 style={{ fontSize: "1.2rem", margin: 0 }}>🛡️ Tactical Emission Control (EMCON) Posture</h2>
          <span style={{ fontFamily: "var(--mono)", fontSize: "0.8rem", color: "var(--accent)" }}>
            CURRENT: EMCON {emconLevel}
          </span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1rem" }}>
          {[
            {
              level: "ALPHA",
              title: "EMCON Alpha (Full Radio Silence)",
              desc: "Zero active RF emissions. Radar, transponders, and omni-SATCOM disabled to defeat foreign ELINT and dark fleet intercept.",
            },
            {
              level: "BRAVO",
              title: "EMCON Bravo (Low-Probability Intercept)",
              desc: "Directional laser/narrow-beam SATCOM only. Encrypted burst telemetry with Doppler dispersion and frequency hopping.",
            },
            {
              level: "CHARLIE",
              title: "EMCON Charlie (Normal Active)",
              desc: "Full maritime radar, AIS transponder broadcasts, and standard Starlink/SATCOM operational connectivity.",
            },
          ].map((item) => {
            const isSelected = emconLevel === item.level;
            return (
              <button
                key={item.level}
                onClick={() => setEmconLevel(item.level as any)}
                style={{
                  background: isSelected ? "var(--panel-2)" : "transparent",
                  border: isSelected ? "2px solid var(--accent)" : "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "1rem",
                  textAlign: "left",
                  cursor: "pointer",
                }}
              >
                <div
                  style={{
                    color: isSelected ? "var(--accent)" : "var(--text)",
                    fontWeight: 700,
                    fontSize: "0.95rem",
                    marginBottom: "0.3rem",
                  }}
                >
                  {item.title}
                </div>
                <div style={{ color: "var(--muted)", fontSize: "0.82rem", lineHeight: 1.5 }}>{item.desc}</div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Two Column Section: Dark Fleet & Orbital SAR Passes */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        {/* Dark Fleet Contacts Panel */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.5rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.2rem", margin: 0 }}>🚢 Dark Fleet Radar Contacts</h2>
            <span style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--muted)" }}>
              Sensor: Coastal HF Radar &amp; AIS
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
            {SAMPLE_DARK_CONTACTS.map((c) => (
              <div
                key={c.id}
                style={{
                  background: "var(--panel-2)",
                  border: c.threatScore > 0.7 ? "1px solid rgba(248, 113, 113, 0.4)" : "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "1rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                  <strong style={{ color: "var(--text)", fontFamily: "var(--mono)" }}>{c.id}</strong>
                  <span
                    style={{
                      background:
                        c.aisStatus === "ACTIVE"
                          ? "rgba(74, 222, 128, 0.15)"
                          : "rgba(248, 113, 113, 0.15)",
                      color: c.aisStatus === "ACTIVE" ? "var(--accent-2)" : "var(--danger)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      padding: "0.15rem 0.5rem",
                      borderRadius: "4px",
                    }}
                  >
                    {c.aisStatus}
                  </span>
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  Speed: {c.speed} kts • Distance: {c.distanceKm} km • Position: {c.lat}°N, {c.lon}°W
                </div>
                <div style={{ marginTop: "0.5rem", display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
                  {c.anomalies.map((a, i) => (
                    <span
                      key={i}
                      style={{
                        background: "rgba(255, 0, 60, 0.1)",
                        color: "#ff4d6d",
                        fontSize: "0.72rem",
                        fontFamily: "var(--mono)",
                        padding: "0.1rem 0.4rem",
                        borderRadius: "3px",
                      }}
                    >
                      {a}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Orbital SAR Reconnaissance Passes Panel */}
        <div
          style={{
            background: "var(--panel)",
            border: "1px solid var(--border-strong)",
            borderRadius: "12px",
            padding: "1.5rem",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.2rem", margin: 0 }}>🛰️ Orbital SAR / Recon Passes</h2>
            <span style={{ fontSize: "0.75rem", fontFamily: "var(--mono)", color: "var(--muted)" }}>
              Orbital Ephemeris Tracking
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
            {SAMPLE_SATELLITE_PASSES.map((p) => (
              <div
                key={p.id}
                style={{
                  background: "var(--panel-2)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  padding: "1rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                  <strong style={{ color: "var(--accent)" }}>{p.satellite}</strong>
                  <span
                    style={{
                      fontFamily: "var(--mono)",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      color: p.exposureScore > 0.7 ? "var(--accent-3)" : "var(--accent-2)",
                    }}
                  >
                    {(p.exposureScore * 100).toFixed(0)}% Exposure
                  </span>
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  Sensor: {p.sensor} • Max Elevation: {p.elevationDeg}° • Window: {p.durationMins} mins
                </div>
                <div
                  style={{
                    marginTop: "0.5rem",
                    padding: "0.4rem 0.6rem",
                    background: "rgba(56, 189, 248, 0.05)",
                    borderLeft: "2px solid var(--accent)",
                    fontSize: "0.8rem",
                    color: "var(--text)",
                  }}
                >
                  🛡️ Directive: {p.maskingDirective}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
        <Link href="/environmental-risk" className="btn btn-primary">
          Inspect Environmental &amp; Permafrost Risks →
        </Link>
        <Link href="/canadian-corridors" className="btn btn-ghost">
          Back to Canadian Corridors
        </Link>
      </div>
    </div>
  );
}
